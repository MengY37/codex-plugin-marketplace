#!/usr/bin/env python3
"""Validate this marketplace: marketplace.json plus every plugin manifest and skill."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"

NAME_RE = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$")
MARKETPLACE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
INSTALL_POLICIES = {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
AUTH_POLICIES = {"ON_INSTALL", "ON_USE"}
REQUIRED_INTERFACE_FIELDS = (
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
)


def load_json(path: Path, errors: list[str]) -> dict | None:
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"{path.relative_to(ROOT)} is not valid JSON: {error}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.relative_to(ROOT)} must contain a JSON object")
        return None
    return payload


def require_string(payload: dict, key: str, where: str, errors: list[str]) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: `{key}` must be a non-empty string")
        return None
    return value


def validate_skill(skill_md: Path, errors: list[str]) -> None:
    relative = skill_md.relative_to(ROOT)
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{relative}: SKILL.md must start with YAML frontmatter")
        return
    end = text.find("\n---", 3)
    if end == -1:
        errors.append(f"{relative}: SKILL.md frontmatter is not closed")
        return
    frontmatter = text[3:end]
    for field in ("name", "description"):
        match = re.search(rf"^{field}\s*:\s*\S", frontmatter, re.MULTILINE)
        if match is None:
            errors.append(f"{relative}: frontmatter is missing `{field}`")


def validate_plugin(plugin_name: str, expected_path: str, errors: list[str]) -> None:
    plugin_root = (ROOT / expected_path).resolve()
    if ROOT not in plugin_root.parents:
        errors.append(f"{plugin_name}: source path escapes the repository")
        return
    if not plugin_root.is_dir():
        errors.append(f"{plugin_name}: source path {expected_path} does not exist")
        return

    manifest = load_json(plugin_root / ".codex-plugin" / "plugin.json", errors)
    if manifest is None:
        return
    where = f"{plugin_name}/.codex-plugin/plugin.json"
    manifest_name = require_string(manifest, "name", where, errors)
    if manifest_name is not None and manifest_name != plugin_name:
        errors.append(f"{where}: `name` must match the plugin folder name `{plugin_name}`")
    if manifest_name is not None and NAME_RE.fullmatch(manifest_name) is None:
        errors.append(f"{where}: `name` contains invalid characters")

    version = require_string(manifest, "version", where, errors)
    if version is not None and SEMVER_RE.fullmatch(version) is None:
        errors.append(f"{where}: `version` must be strict semver")
    require_string(manifest, "description", where, errors)

    author = manifest.get("author")
    if not isinstance(author, dict):
        errors.append(f"{where}: `author` must be an object")
    else:
        require_string(author, "name", f"{where} author", errors)

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{where}: `interface` must be an object")
    else:
        for field in REQUIRED_INTERFACE_FIELDS:
            require_string(interface, field, f"{where} interface", errors)
        if "defaultPrompt" not in interface and "default_prompt" not in interface:
            errors.append(f"{where}: `interface.defaultPrompt` is required")
        capabilities = interface.get("capabilities")
        if not isinstance(capabilities, list) or not all(
            isinstance(value, str) and value.strip() for value in capabilities
        ):
            errors.append(f"{where}: `interface.capabilities` must be an array of strings")

    skills_dir = plugin_root / "skills"
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            validate_skill(skill_md, errors)


def validate_marketplace() -> list[str]:
    errors: list[str] = []
    marketplace = load_json(MARKETPLACE_PATH, errors)
    if marketplace is None:
        return errors

    where = ".agents/plugins/marketplace.json"
    name = require_string(marketplace, "name", where, errors)
    if name is not None and MARKETPLACE_NAME_RE.fullmatch(name) is None:
        errors.append(f"{where}: `name` may only contain letters, digits, `_` and `-`")

    interface = marketplace.get("interface")
    if interface is not None:
        if not isinstance(interface, dict):
            errors.append(f"{where}: `interface` must be an object")
        else:
            require_string(interface, "displayName", f"{where} interface", errors)

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        errors.append(f"{where}: `plugins` must be an array")
        return errors

    seen: set[str] = set()
    for index, entry in enumerate(plugins):
        entry_where = f"{where} plugins[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_where} must be an object")
            continue
        plugin_name = require_string(entry, "name", entry_where, errors)
        if plugin_name is not None:
            if NAME_RE.fullmatch(plugin_name) is None:
                errors.append(f"{entry_where}: invalid plugin name")
            if plugin_name in seen:
                errors.append(f"{entry_where}: duplicate plugin entry `{plugin_name}`")
            seen.add(plugin_name)

        source = entry.get("source")
        source_path = None
        if not isinstance(source, dict):
            errors.append(f"{entry_where}: `source` must be an object")
        else:
            if source.get("source") != "local":
                errors.append(f"{entry_where}: `source.source` must be `local`")
            source_path = source.get("path")
            expected = f"./plugins/{plugin_name}"
            if source_path != expected:
                errors.append(f"{entry_where}: `source.path` must be `{expected}`")

        policy = entry.get("policy")
        if not isinstance(policy, dict):
            errors.append(f"{entry_where}: `policy` must be an object")
        else:
            if policy.get("installation") not in INSTALL_POLICIES:
                errors.append(
                    f"{entry_where}: `policy.installation` must be one of {sorted(INSTALL_POLICIES)}"
                )
            if policy.get("authentication") not in AUTH_POLICIES:
                errors.append(
                    f"{entry_where}: `policy.authentication` must be one of {sorted(AUTH_POLICIES)}"
                )

        require_string(entry, "category", entry_where, errors)

        if plugin_name is not None and isinstance(source_path, str):
            validate_plugin(plugin_name, source_path, errors)

    return errors


def main() -> int:
    errors = validate_marketplace()
    if errors:
        print("Marketplace validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Marketplace validation passed: {MARKETPLACE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
