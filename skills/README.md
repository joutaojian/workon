# 技能目录

本目录存放内置示例技能。每个技能是一个独立子目录，包含：

```
<skill-id>/
  manifest.json   # 技能契约：id、名称、标签、输入/输出、入口命令、超时等
  run.py          # 实际执行脚本（任意语言，由 manifest 的 entry 指定）
  README.md       # 可选说明
  requirements.txt# 可选依赖声明
```

你的私有工作脚本**不要**放进这个目录。把它们放在另一个 git 项目里，通过
`python -m workon skill add <私有目录>` 或 Web「设置」页登记，workon 会像读取内置
技能一样扫描它们。这样开源仓库保持干净，工作脚本留在你的私有仓库。

详见项目根目录 `README.md` 与 `docs/skill-format.md`。
