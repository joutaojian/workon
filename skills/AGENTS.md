# AGENTS.md — skills/

只放**通用示例技能**（如 `text-echo`）。勿放私有业务脚本、真实业务数据（见 CONTRIBUTING.md 安全红线）。

## 约束

- 每个技能 = 一个目录：`manifest.json` + `run.py` + `README.md`，遵循 [docs/skill-format.md](../docs/skill-format.md) 契约 v0.2。
- 新示例先 `workon init <目录>` 生成契约，`workon skill validate <目录>` 通过才算合格。
- 示例必须自包含：纯标准库优先；确需第三方依赖要在 README 顶部注明。
- 脚本非交互、幂等：退出码 0 为成功，输出写当前工作目录。
