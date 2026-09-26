---
name: plugin-authoring
description: Add or update a plugin in this GitHub-hosted Codex plugin marketplace. Use when the user asks to create a new plugin here, register an existing plugin in the marketplace, or check that the marketplace files are valid.
---

# Authoring a plugin for this marketplace

Use this skill when someone wants to add a plugin to this repository or verify that the
marketplace is still valid.

## Required layout

```
.agents/plugins/marketplace.json          # marketplace catalogue
plugins/<plugin-name>/.codex-plugin/plugin.json
plugins/<plugin-name>/skills/<skill-name>/SKILL.md
```

The plugin folder name, `plugin.json` `name`, and the marketplace entry `name` must be identical.
Use lowercase hyphen-case, at most 64 characters, matching `[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*`.

## Adding a plugin

1. Copy the template plugin: `cp -r plugins/example-plugin plugins/<plugin-name>`.
2. Edit `plugins/<plugin-name>/.codex-plugin/plugin.json`:
   - `name` must equal the folder name.
   - `version` must be strict semver such as `0.1.0`; never leave the template version in place
     for a plugin you intend to publish.
   - `description`, `author.name` and every `interface` field
     (`displayName`, `shortDescription`, `longDescription`, `developerName`, `category`,
     `defaultPrompt`, `capabilities`) need real values. Keep at most three `defaultPrompt`
     entries, each short enough to scan in the composer.
   - Keep `skills` pointing at `./skills/` when the plugin ships skills.
3. Replace the template skill with your own `skills/<skill-name>/SKILL.md`. The file needs
   frontmatter with a `name` and a `description` that says what the skill does and when to use it.
4. Append the plugin to `.agents/plugins/marketplace.json`:

   ```json
   {
     "name": "<plugin-name>",
     "source": { "source": "local", "path": "./plugins/<plugin-name>" },
     "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
     "category": "Productivity"
   }
   ```

   Append instead of reordering: the array order is the render order in Codex. Only add
   `policy.products` when product gating is explicitly requested.
5. Run `python scripts/validate.py` and fix everything it reports before committing.

## Installing from this marketplace

```bash
codex plugin marketplace add <owner>/<repo>
codex plugin add <plugin-name>@<marketplace-name>
```

After installing or reinstalling a plugin, tell the user to start a new conversation so Codex
picks up the plugin's skills and tools.
