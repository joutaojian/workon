# AGENTS.md — workon/official_skills/

⭐ 官方能力目录，随包分发，面向非技术文员的高频确定性任务。当前 5 个：`pdf-tool`（PDF 合并/拆分，另有自己的 AGENTS.md）、`word-count`（文稿字数统计）、`text-tidy`（文本整理）、`csv-tool`（表格整理）、`batch-rename`（文件批量重命名）。

## 约束（所有官方技能通用）

1. **不可删除、不可改 id**：`official: true`、`author: workon`、`version: 1.0.0`，UI 带「★ 官方能力」徽章、不可覆盖。
2. **纯 Python 标准库**：`dependencies` 必须为 `[]`；不联网、不装第三方包。csv/xlsx 读写一律 zipfile + xml 自实现（见 `csv-tool/run.py`）。
3. **manifest 遵循 [docs/skill-format.md](../../docs/skill-format.md) 契约 v0.2**：输出声明的 `type` 与落盘路径一致（file 用 path 指定文件名、dir 用 path 指定目录名）；entry 占位符 `{字段名}` 必须在 inputs/params 中声明；多值输入整条 arg 为占位符。
4. **输出文件名是对外契约**，不能改：pdf-tool `merged.pdf` / `split_pages`、word-count `word-count-report.json`、text-tidy `tidied/`、csv-tool `result.csv` / `result.xlsx`、batch-rename `renamed/`。
5. **run.py 非交互**：退出码 0 为成功；stdout 输出中文摘要（子进程 utf-8 收流，Windows 控制台编码无关）；不动用户原文件（batch-rename 产出副本）。
6. **改动后复测**：`python -m unittest discover -s tests`（含 tests/test_official_skills.py）+ `python -m workon skill validate <技能目录>` + `python -m workon skill run <id> --file files=… --param k=v` 真实样例各模式跑一遍。

## 新增官方技能

放 `workon/official_skills/<id>/`（manifest.json + run.py + README.md），pyproject package-data glob 自动打包；面向非技术文员「确定性、可重复」的问题（数字数、整理文档、合表、改文件名类），需要 AI 创作的问题不要做成官方技能。
