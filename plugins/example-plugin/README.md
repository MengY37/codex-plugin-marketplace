# example-plugin

这个插件是仓库里的**模板**：它自己能用（带一个 `plugin-authoring` 技能），同时也能当作你新建插件时的起点。

## 结构

```
example-plugin/
├─ .codex-plugin/plugin.json   # 清单：name / version / description / author / interface
├─ skills/plugin-authoring/    # 技能目录，每个子目录一个技能
└─ README.md
```

## 改造成你自己的插件

1. `cp -r plugins/example-plugin plugins/my-tools`
2. 把 `plugin.json` 的 `name` 改成 `my-tools`，并更新 `description`、`author`、`interface`；
3. 把 `skills/plugin-authoring` 换成你自己的技能目录；
4. 在仓库根目录的 `.agents/plugins/marketplace.json` 里追加一条 `my-tools` 的记录；
5. 运行 `python scripts/validate.py` 确认无误。

## 使用

安装后新开一个对话，然后直接说你想做的事；Codex 会根据技能里的 `description` 决定是否加载它。
