# 变更日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## Unreleased

### 变更
- **官方能力收敛为仅 pdf-tool**：按要求移除 `word-count` / `text-tidy` / `csv-tool` / `batch-rename` 四个非 PDF 官方技能，`workon/official_skills/` 现只保留 `pdf-tool`。同步更新 `tests/test_official_skills.py`（期望 1 个技能、id 集合仅 `pdf-tool`）及 AGENTS.md / README.md / AGENT-GUIDE.md / CHANGELOG 相关文档口径。
- **召唤表单全中文**：字段标题取 manifest 的可选 `label`（中文显示名，缺省退回 `name`，不改执行占位符）；下拉选项取可选 `choices_labels`（显示中文、提交值仍是真实 `choices` 值）；文件选择改为中文按钮「＋ 选择文件 / 选择文件夹」并回显所选中文件名，去掉浏览器原生的 "Choose Files / No file chosen"；技能下拉去掉 `(id)` 英文后缀。`pdf-tool` 的 `files` / `mode` / `pages` 分别标注「PDF 文件 / 处理模式 / 页码范围」，模式选项显示「合并多个 PDF / 拆分为多个单页 PDF」。`docs/skill-format.md` 补充 `label` / `choices_labels` 字段说明。
- **技能库移除统计卡**：移除技能库页顶部「可用技能 / 标签数量 / 技能来源」三张统计卡及其 CSS/JS（`workon/web_pages.py`）。
- **使用指引新增「复制回 AI」第三段话术**：工作台「使用指引」从两段扩为三段，新增「反过来 · 复制回 AI 执行」卡片，示例把已固化技能（文本回显）连同脚本路径、工作目录、输入与复现命令一次性复制回任意 AI，让它按固定脚本直接复现、勿重新发明（话术与技能卡「复制给 AI」口径一致）。标题与说明同步改为三段（`workon/web_pages.py`）。
- **安装话术加国内网络兜底**：给外部 AI Agent 的安装话术（首页 / 工作台使用指引 / README 三处逐字一致）末尾补一段提示——pip 装依赖优先走清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`；GitHub 直连 clone 报 CONNECT 502 / 超时时，把原始 clone 地址完整拼在镜像前缀（如 `https://ghfast.top/`）后再克隆，失效可换 `https://gh-proxy.com/` / `https://ghproxy.net/` 或自搜最新镜像。README 命令行安装区同步加镜像说明与示例命令（实测场景：Agent 照话术安装时被企业网络拦 GitHub、pip 源受限）。

## 0.4.0 (2026-11-22)

新增首页、密码登录与 5 个官方能力，并补齐「技能版本 + 更新检查」，同时修复外部 Agent 分发链路上的一组真实缺陷（由独立审查 + 端到端实测发现）。全部已实现并实测通过。

### 新增
- **首页 + 密码登录**：打开 `http://localhost:8080` 先看到首页，展示使用方案（AI 做一次 → 人确认一次 → 固化为技能 → 反复召唤）与特性；点「进入工作台」后用密码登录（默认 `workon`，页面有提示，登录后可在「设置」修改，也可用环境变量 `WORKON_PASSWORD` 预设）。
  - 新增 `workon/pages.py`：`HOME_HTML`（深色赛博风、纯 CSS 渐变光斑 + SVG 噪点，无 WebGL/隐藏光标/外部资源）与 `LOGIN_HTML`（浅色玻璃拟态，仅一个密码字段）。
  - 鉴权守卫：`/`、`/login`、`/health`、`/static/*` 公开；`/api/*` 未登录返回 401；其余页面未登录重定向 `/login`。session secret 持久化 `data/secret.key`，密码用 `hmac.compare_digest` 校验，COOKIE 设 HttpOnly + SameSite=Lax。
- **⭐ 官方能力「PDF 合并与拆分」**：内置 `workon/official_skills/pdf-tool/`，纯标准库实现（无需 WPS/Adobe、无需联网、零第三方依赖），支持多 PDF 合并与按页码范围拆分。manifest 新增 `official` 标记，UI 带橙色官方徽章、置顶展示、不可覆盖/删除，与用户自己添加的私有技能明确区分。
- **⭐ 官方能力扩到 5 个**：`workon/official_skills/` 从 pdf-tool 一个扩为五个，全部纯标准库、官方徽章、不可覆盖/删除，面向非技术文员高频问题——`word-count` 文稿字数统计（txt/md/docx）、`text-tidy` 文本整理（去空行/替换词句）、`csv-tool` 表格整理（合并/去重/排序，csv+xlsx 读写内置）、`batch-rename` 文件批量重命名（前缀/后缀/替换/编号）。全部经真实样例复测（skill validate + skill run + xlsx 读写往返）。
- **工作台「使用指引」页**：`workon/web.py` 工作台新增默认首页「使用指引」（按设计图实现）——左侧 GET STARTED 说明，右侧两张话术卡（「第一次 · 装好并开始」「以后 · 固化成技能」），一键复制发给 AI 助手，非技术用户不用读文档就能上手。
- **技能卡「📋 复制给 AI」**：每张技能卡可一键复制一段含脚本绝对路径与提示的话术，粘贴给任意 AI 参考执行。
- 新增 `tests/test_official_skills.py`：官方能力回归（恰好 5 个目录且 id 集合固定、manifest 契约合法、`official:true`、纯标准库、run.py/README.md 在位）。
- 移除工作台中所有「员工」隐喻文案（用户要求）。
- **AGENTS.md 系列**：新增根目录 `AGENTS.md`（项目地图 + 硬性约束 + 改动验收）与 `workon/official_skills/pdf-tool/`、`skills/`、`workon/skills/workon-capture/` 三个子目录 AGENTS.md（各自的职责与限制），供接入本仓库的 AI Agent 遵守。
- **两层版本号**：执行引擎 `workon.__version__`，技能说明书 `install.SKILL_VERSION`（当前 `1.0.0`），安装时写入 `SKILL.md` 的 `metadata.version`，各自独立演进。
- `workon update-check`：只读检查引擎与已装进各 Agent 的技能是否需要更新，支持 `--agent` / `--offline`；断网自动降级，不抛栈、不改文件。
  - 上游查询顺序：GitHub Releases → GitHub Tags → PyPI。**PyPI 上的 `workon` 属于另一个项目**，更新检查会校验归属并忽略它，避免误导用户 `pip install -U` 装错包。本项目尚未发布到 PyPI，请以 GitHub 仓库为准。
- 安装器生成 `workon.cmd` / `workon.sh` 启动器（无需依赖 console script 也能在任意目录调用）与 `.workon-install.json` 安装记录。

### 变更
- **首页「开始」区块改版**：原「在你的本机，几步开始」（终端命令）改为「开始只需要两段话」，前移至首屏之后最前位置——面向非技术用户：第一段话用于让 AI 助手装好 workon 并固化第一件技能，第二段话用于以后每次把重复做的事固化成技能，均可一键复制发给 AI 助手，无需接触命令行；首屏描述同步改为通俗说法（「AI 帮你做一次，你点头确认……点一下『召唤』……」）。
- **Web UI 换橙黑主题**：工作台（`workon/web.py` `INDEX_HTML`）重写并改为黑底橙色高亮（`--accent:#ff7a1a` / `--bg:#14110f`），首页与登录页同步换色；仍为纯 CSS、无外部资源。
- **README 面向对象 + 只留重点**：人类部分新增「面向对象」（不写代码的文员、助理、办公人员），并按用户指定的重点清单裁剪——只留「一句话说明 / 上手就靠两段话 / 日常网页点召唤」，删 FAQ 三则与过程性解释；两段话术与首页、工作台使用指引逐字一致；文档细节保留在下方 AI/开发者区。
- `Skill` 数据类新增 `official: bool` 字段，`public()` 暴露；`config.py` 强制注入内置 `skills` + `official_skills` 两个目录，不可从配置移除。

### 架构整理
- **工作台 HTML 独立成模块**：`web.py` 的 `INDEX_HTML` 搬到 `workon/web_pages.py`（`WORKBENCH_HTML`，`__VERSION__` 运行时注入），`web.py` 从 ~800 行降到 347 行，职责更清晰；HTML 仍是 raw string、纯 CSS、零外部资源，反斜杠转义原样保留。
- **路径与魔数收敛**：超时默认值集中到 `config.DEFAULT_TIMEOUT`（`models` / `capture` / `settings` 共用）；`runner` 的 run_id 长度、超时上限、错误/输出截断长度改为具名常量；`storage.init_db` 加幂等缓存避免每次查询重复建表。
- **占位符规则统一**：`models.PLACEHOLDER_PATTERN` 成为唯一校验/执行规则，`_RESERVED_PLACEHOLDERS` 补全执行器注入的 `workdir` / `skill_dir` / `run_id`，杜绝「校验放行、运行不展开」。
- **更新检查归属修正**：`_pypi_is_ours` 改查 `project_urls` 的值（URL）而非键名，避免误判 PyPI 同名项目。
- **文档与工程规范**：新增 `SECURITY.md`；`.gitignore` 补 `build/` / `dist/` / `*.db`；`CONTRIBUTING.md` 验收补 unittest；修正两处 AGENTS.md 相对链接；skill-format 标注 `source` 为标注字段；`docs/skill-format.md` 与 CHANGELOG 同步七步协议口径。

### 修复
- **技能源随包分发**：把 `workon-capture/SKILL.md` 从仓库根 `skills/` 移入核心包 `workon/skills/`，`pyproject.toml` 加 `package-data`；非 editable 的 `pip install` 后 `install-skill` 不再报「找不到技能源文件」。
- **安装后命令可用**：SKILL.md 里所有命令改用 `{{WORKON}}` 占位符，安装时替换成真实启动器路径，修复外部 Agent 在任意目录执行报 `No module named workon` 及 `<子命令>` 占位符导致的 shell 语法错误。
- **断链符号链接**：`uninstall` 能清理已断开的目标符号链接；`--force` 不再写穿指向别处的符号链接。
- **frontmatter 健壮性**：容忍 BOM 与前导空行，用正则精确闭合 frontmatter，避免正文里的 `---` 被误判；Windows 写文件用 `newline=""` 防止 `\r\r\n`。
- **退出码与返回体**：`skipped-exists` 退出码改为 2（与真失败区分），返回值拆成 `changed/unchanged/skipped/failed`；`uninstall` 失败退出码不再恒为 0。
- **Python 3.12+**：`shutil.rmtree` 按版本分流 `onexc` / `onerror`，消除废弃告警。
- **pip 安装噪音**：内置技能目录 `_builtin_skill_dir()` 优先仓库根、回落包内目录，消除每次命令刷「技能目录不存在」的 stderr。
- 更新 `pyproject.toml` 的仓库地址为 `github.com/joutaojian/workon`（原 `tajok/workon` 实测 404）。

## 0.3.0 (2026-11-22)

面向「让外部 AI Agent 自己把工作固化进 workon」的分发能力。

### 新增
- `workon install-skill` / `uninstall-skill`：把 `skills/workon-capture/SKILL.md` 按 [Agent Skills 开放标准](https://agentskills.io/specification) 装进 Claude Code、Codex、Qoder、通用 `~/.agents/skills`、WorkBuddy 的用户级 skills 目录，并在安装时注入本机 workon 项目路径与解释器路径。
- `pyproject.toml`：可 `pip install -e .` 获得 `workon` 命令，摆脱「必须先 cd 到项目根」的限制；Web 依赖仍为可选项。
- `workon-capture` 技能补「输出写相对路径」章节：脚本写文件要走相对路径并在 manifest 声明 `outputs[].path`，否则输出不进 `data/runs/<run_id>/outputs/`。

### 变更
- `AGENT-GUIDE.md` 第 3 节改为一条命令安装到各 Agent，并列出五个目录约定与「换位置后需 `--force` 重装」的提示。

## 0.2.0 (2026-11-21)

面向「固定输入输出、标签分类、外部目录加载」的固化协议升级，降低普通文员与 AI 编码助手的使用门槛。

### 新增
- 多维输入输出：在 text/file/docx/xlsx 之外新增 json、image、dir 类型，并支持 `multiple` 多值字段，覆盖批量文件与目录场景。
- 新增 `workon capture` 命令：把一次现有执行固化为可复用技能草稿；新增 `workon init` 命令：从零初始化技能目录骨架。
- Web 新增 `/api/capture` 接口，支持在网页端完成技能固化。
- 面向 Codex / WorkBuddy / Qoder 的固化协议与 `AGENT-GUIDE`：约定 AI 编码助手如何按契约生成、校验并登记技能。
- 普通文员低门槛流程：从「跑一次 → 捕获 → 命名打标签 → 一键召唤」的傻瓜化操作步骤说明。

### 变更
- 存储强制为 SQLite-only：执行历史统一收敛到标准库 sqlite3，去除其他存储后端选项，核心保持零第三方依赖。

## 0.1.0 (2026-11-21)

首个开源版本：从原内部工作台重构为通用「技能注册与召唤平台」。

### 新增
- 本地技能格式 `manifest.json`：id、标签、text/file/docx/xlsx 输入与输出、入口命令、参数、超时、依赖。
- 技能发现：`skills/` 内置目录 + 任意外部目录（私有 git 仓库），按 id 去重、标签检索。
- 召唤执行器：输入校验、临时目录隔离、命令白名单、占位符替换、超时控制、输出收集。
- 执行历史：SQLite 持久化，CLI 与 Web 均可查询。
- 三种调用方式：CLI（`python -m workon skill ...`）、HTTP API、Web 单页控制台。
- 示例技能 `text-echo`（外部技能目录可通过环境变量或设置页登记）。

### 移除
- 删除全部内部业务脚本、模板、Excel/Word 数据与明文凭证（数据库口令、Coze/钉钉/邮箱令牌等）。
- 依赖从数十个业务库精简为：核心零依赖，Web 仅可选 Flask。

> 发布提示：原仓库 git 历史中含有已删除的凭证，开源前请轮换全部凭证并清理历史或新建仓库。详见 README「安全须知」。
