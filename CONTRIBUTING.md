# 贡献指南

欢迎为 workon 贡献代码、技能示例或文档。

## 开发准备

```bash
git clone <your-fork-url> workon
cd workon
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                     # 仅 Web 需要 Flask
```

核心功能（CLI 与技能执行）不依赖第三方库，Python 3.9+ 即可运行。

## 项目结构

```
workon/        核心包（配置、技能模型、注册表、执行器、存储、CLI、Web）
skills/        内置示例技能（请勿提交私有业务脚本）
docs/          设计与格式文档
```

## 提交规范

- 先开 issue 讨论较大改动。
- 每个 PR 聚焦一件事，附带测试与文档更新。
- 提交前运行验收：`python -m compileall -q workon` 确保语法正确，`python -m unittest discover -s tests` 确保测试全绿。

## 添加技能示例

欢迎提交通用、无业务敏感数据的技能示例到 `skills/`。请遵循 [技能格式规范](docs/skill-format.md)，
并附带 `README.md` 说明输入、输出与运行方式。真实业务脚本请放在你自己的私有仓库，通过外部目录登记使用。

## 安全

切勿把口令、令牌、内网地址、真实业务数据提交到本仓库。发现泄露请立即通过 issue 私聊维护者。
