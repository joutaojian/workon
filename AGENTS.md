# AGENTS.md

面向在本仓库（workon）内工作的 AI 编码 Agent：项目地图、硬性约束、改动验收。给人看的入口是 [README.md](README.md)；技能固化协议见 [AGENT-GUIDE.md](AGENT-GUIDE.md)；manifest 契约见 [docs/skill-format.md](docs/skill-format.md)。

## 项目是什么

workon 是开源、本地优先的「AI 产出冻结层」：AI 做一次、人工确认一次，把固定脚本 + manifest 冻结成技能；之后填输入确定性复现，**不再调用 AI**。

- Python 3.9+；核心零依赖（仅标准库），Flask 仅 Web 功能可选
- 两层版本号：`workon/__init__.py` `__version__`（引擎）与 `workon/install.py` `SKILL_VERSION`（说明书）
- manifest 契约 v0.2：输入 text/file/docx/xlsx/json/image/dir，输出 text/file/docx/xlsx/json/dir，可 multiple

## 仓库地图

| 路径 | 作用 |
| --- | --- |
| `workon/` | 核心包：config / models / registry / runner / storage / capture / install / update / cli / web / pages |
| `workon/pages.py` | 首页 / 登录页 HTML（`HOME_HTML`、`LOGIN_HTML`） |
| `workon/web.py` | Flask Web/API，`INDEX_HTML` 技能工作台 |
| `workon/official_skills/` | ⭐ 官方能力仅 pdf-tool（PDF 合并/拆分），约束见其 `AGENTS.md`（目录级与 pdf-tool 各有一份） |
| `workon/skills/workon-capture/` | 给外部 Agent 的说明书源 `SKILL.md`，有自己的 AGENTS.md |
| `skills/` | 内置示例技能，有自己的 AGENTS.md |
| `tests/` | `python -m unittest discover -s tests`（10 个用例，含官方技能回归） |
| `docs/` | `skill-format.md`（manifest 契约）等设计文档 |

## 硬性约束（限制）

1. **HTML 必须保持 raw string**：`workon/pages.py`、`workon/web.py` 的 HTML 都是 `r"""`。反斜杠照现状写：JS 换行转义是单反斜杠 `join('\n')`，路径正则是 `split(/[\\/]/)`；禁止「顺手修正」转义——项目曾因此出过 bug。
2. **页面零外部资源**：不引 CDN、外链字体、外链图片，纯 CSS（`tests/test_web_pages.py` 检查此项）。
3. **核心零依赖**：`workon/` 只用标准库；Flask 仅 `web.py` 可选导入。不给核心加第三方依赖。
4. **兼容 Python 3.9+**：不用 `match`、`int | str` 等 3.10+ 语法。
5. **安全红线**：不提交口令、令牌、内网地址、真实业务数据；`data/` 是运行时数据（`workon.db`、`secret.key`、`runs/`），不入库、不手改。
6. **官方能力不可动**：`workon/official_skills/` 下仅保留 pdf-tool，保持 `official: true`、纯标准库、`dependencies: []`、不可删除；其输出文件名是对外契约（`merged.pdf` / `split_pages`）。
7. **`{{WORKON}}` 占位符原样保留**：详见 `workon/skills/workon-capture/AGENTS.md`。
8. **固化协议的人工确认关卡不可绕过**：`capture --yes` 之前必须由人确认（AGENT-GUIDE.md 七步协议）。
9. **UI 主题橙黑**：`--accent:#ff7a1a`、`--bg:#14110f`、`--surface:#1e1a17`、`--text:#ddd2c6`、`--title:#fff4e8`；样式改动沿用这套 CSS 变量，保持纯 CSS。
10. **API / 鉴权约定不动**：`/api/*` 统一返回 `{"code":0,"message","data"}`；`before_request` 鉴权（`/`、`/login`、`/health`、`/static/*` 公开；`/api/*` 未登录 401；其余重定向 `/login`）默认不变。

## 改动验收（每次提交前）

```bash
python -m compileall -q workon
python -m unittest discover -s tests
```

改了 Web UI 时另起实例目检（旧的 serve 进程发的是旧页面，需换端口或重启后才生效）：

```bash
python -m workon serve --port <空闲端口>
```

## 文档同步

- 面向用户的行为变化 → README（人类部分保持精简）+ `CHANGELOG.md` Unreleased 段
- 说明书 `SKILL.md` 内容变化 → 考虑同步 `SKILL_VERSION` 与 CHANGELOG
