# AGENTS.md — workon/skills/workon-capture

`SKILL.md` 是「给外部 AI Agent 的说明书源」，由 `install-skill` 安装时注入本机信息后复制到各 Agent 目录（~/.claude、~/.agents、~/.qoder、~/.workbuddy）。

## 约束

1. **`{{WORKON}}` 占位符原样保留**（`workon/install.py:53` `_PLACEHOLDER = "{{WORKON}}"`）：正文里所有 `{{WORKON}}` 不得替换、不得删除——安装时才替换成带引号的本机启动器路径。
2. **frontmatter 的 version 不手改**：由 `install.py` `_with_version()` 注入 `SKILL_VERSION`（当前 1.0.0）；说明书内容变更时同步考虑 bump `SKILL_VERSION` 与 CHANGELOG。
3. **固化协议七步与人工确认关卡的措辞不可省略**：「确认保存成技能」是全程唯一人工关卡，必须排在 `capture --yes` 之前（协议正文见 [AGENT-GUIDE.md](../../../AGENT-GUIDE.md)）。
4. frontmatter 遵循 agentskills.io 规范（name / description）；描述要写明触发场景，供外部 Agent 路由。
