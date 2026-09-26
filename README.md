# Codex Plugins — 一个 GitHub 托管的插件市场

这是一个可以直接用 GitHub 托管、由 Codex 直接读取的**插件市场（marketplace）**仓库。
别人（或者你自己的另一台电脑）只要一条命令，就能把这个市场加进来，然后安装里面的插件。

## 一、安装这个市场

```bash
# 把市场添加到 Codex
codex plugin marketplace add MengY37/codex-plugin-marketplace

# 查看市场里有哪些插件
codex plugin list

# 安装其中的插件
codex plugin add example-plugin@codex-plugins
```

装好之后，**新开一个对话**，Codex 就能加载这个插件里的技能了。

## 二、目录结构

```
.
├─ .agents/plugins/marketplace.json   # 市场清单：市场的名字 + 插件列表
├─ plugins/
│  └─ example-plugin/                 # 一个插件
│     ├─ .codex-plugin/plugin.json    # 插件清单（必填）
│     ├─ skills/                      # 插件里的技能
│     └─ README.md
├─ scripts/validate.py                # 本地校验脚本
└─ .github/workflows/validate.yml     # push / PR 时自动校验
```

关键约定：

- `marketplace.json` 里的 `source.path` 永远是相对市场根目录的 `./plugins/<插件名>`；
- 插件目录名、`plugin.json` 里的 `name`、`marketplace.json` 里的 `name` 三者必须完全一致；
- 插件的 `version` 必须是严格 semver，例如 `0.1.0`、`1.2.3-beta.1`。

## 三、加一个自己的插件

1. 复制模板插件，改名为你的插件名（小写、连字符，例如 `my-tools`）：

   ```bash
   cp -r plugins/example-plugin plugins/my-tools
   ```

2. 改 `plugins/my-tools/.codex-plugin/plugin.json`：`name`、`version`、`description`、`author`、`interface` 这些字段都要填成真实内容。

3. 删掉模板里的技能，换成你自己的：`plugins/my-tools/skills/<技能名>/SKILL.md`，开头需要 frontmatter：

   ```markdown
   ---
   name: 技能名
   description: 这个技能是干什么的、什么时候该用它
   ---
   ```

4. 把插件登记到市场清单 `.agents/plugins/marketplace.json` 的 `plugins` 数组里（追加到末尾，顺序就是 Codex 里的显示顺序）：

   ```json
   {
     "name": "my-tools",
     "source": { "source": "local", "path": "./plugins/my-tools" },
     "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
     "category": "Productivity"
   }
   ```

5. 校验并提交：

   ```bash
   python scripts/validate.py
   git add -A && git commit -m "Add my-tools plugin"
   git push
   ```

## 四、别人怎么更新

市场是 Git 仓库，所以你在 GitHub 上推了新提交之后，使用者刷新一下就能拿到：

```bash
codex plugin marketplace upgrade codex-plugins   # 拉取市场最新内容
codex plugin add my-tools@codex-plugins          # 安装新插件
```

## 五、本地校验做了什么

`python scripts/validate.py` 会检查：

- `marketplace.json` 的结构、市场名是否合法；
- 每个插件是否都有 `.codex-plugin/plugin.json`，必填字段是否齐全；
- `version` 是否严格 semver；
- 三处 `name` 是否一致，`source.path` 是否指向真实存在的插件目录；
- 每个技能的 `SKILL.md` 是否有 `name` / `description` frontmatter。

CI 会在每次 push 和 PR 时跑同样的检查。

## 许可证

MIT，见 [LICENSE](./LICENSE)。
