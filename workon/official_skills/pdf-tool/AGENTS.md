# AGENTS.md — workon/official_skills/pdf-tool

⭐ 官方能力（`official: true`），随包分发，**不可删除、不可改 id**。免费替代 WPS 的 PDF 合并/拆分。

## 约束

- **纯 Python 标准库**：`dependencies` 必须为空；不联网、不装第三方包。
- **manifest 契约固定**（契约 v0.2）：
  - 输入 `files`（file, ext=pdf, multiple）
  - 参数 `mode`（merge|split，默认 merge）+ `pages`（拆分页码范围，如 `1-3,5,7-9`，留空拆全部）
  - 输出 `merged`（file, `merged.pdf`）+ `pages`（dir, `split_pages`）——**输出文件名是对外契约，不能改**
  - entry 固定 `python run.py --mode {mode} --inputs {files} --pages {pages}`，timeout 120s
- **run.py 必须非交互**：退出码 0 为成功；Windows 中文输出注意 `PYTHONIOENCODING=utf-8`。
- 改动后跑 `python -m unittest discover -s tests`，并用 `skill run pdf-tool` 带真实 PDF 样例试跑（merge 与 split 两种模式）。
