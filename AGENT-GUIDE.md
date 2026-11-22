# workon 固化协议：给 Codex / WorkBuddy / Qoder 等 AI Agent

> 一句话定位：**AI 只负责做一次，人只确认一次，之后由 workon 确定性地复现，不再调用 AI。**

AI 会幻觉、会手抖、每次结果还可能不一样。workon 的角色是「AI 产出的冻结层」：把 AI 这次做对的脚本连同输入样例、依赖文件放进一个目录，用 `workon capture` 固化成一份 manifest 契约。以后再做同样的活，文员只需准备输入、点一下召唤，跑的是**同一份已确认的脚本**，零幻觉、零联网、零 token 费用。

本文件是给 AI Agent 读的操作协议。三种 Agent 通用，命令逐条可复制。

---

## 0. 前提与约定

- 已安装 workon（核心零依赖，Python 3.9+），命令为 `python -m workon ...`（下文统一写作 `workon ...`，两种写法等价）。
- **终端中文编码**：Windows 下先设置 `PYTHONIOENCODING=utf-8`，否则输出中的中文可能乱码。

  ```bash
  # macOS / Linux / Git Bash
  export PYTHONIOENCODING=utf-8
  ```

  ```powershell
  # PowerShell
  $env:PYTHONIOENCODING = "utf-8"
  ```

- 所有路径用**绝对路径**最稳妥；本文用 `D:/work/my-job` 作示例，请替换成真实目录。
- 契约版本为 v0.2；输入类型 `text/file/docx/xlsx/json/image/dir`，输出类型 `text/file/docx/xlsx/json/dir`，字段可带 `multiple: true`。
- 持久化只用本地 SQLite（`data/` 下），不连任何外部数据库。

---

## 1. 完整固化流程（七步，一次完成）

### 第 1 步：AI 完成工作，并把产物收敛到一个目录

AI 先把这次的工作**真正做完并验证正确**，然后把以下东西放进同一个目录（示例 `D:/work/my-job`）：

```
D:/work/my-job/
  run.py               # 主脚本：读输入、写输出
  helper.py            # 可选：依赖脚本
  sample_input.xlsx    # 可选：输入样例，便于以后验证
  requirements.txt     # 可选：脚本自带依赖说明
```

要求：
- 脚本必须能**非交互**运行：所有输入从命令行参数或固定路径读取，不要弹窗、不要 `input()` 等人工输入。
- 脚本写到工作目录的输出要落在**当前目录**（或从参数拿到），因为 workon 每次在临时目录里执行。
- 不要把真实敏感业务数据当样例提交到公共仓库；样例仅用于验证。

### 第 2 步：一次确认（人工关卡）

AI 向人展示：脚本做什么、输入输出是什么、这次跑出来的结果。**必须等人明确说"可以/确认"后再继续固化。** 这一步是整个人机协作中唯一需要人做决定的时刻，之后不再需要 AI。

### 第 3 步：`workon capture` 固化

确认后，扫描目录生成 `manifest.json`（`--yes` 表示非交互直接写入）：

```bash
export PYTHONIOENCODING=utf-8   # Windows PowerShell: $env:PYTHONIOENCODING = "utf-8"

python -m workon capture D:/work/my-job \
  --id my-job \
  --name "我的固定工作" \
  --tags excel,report \
  --entry "python run.py" \
  --yes
```

参数说明：
- `<dir>`：第 1 步的工作目录，必须已存在。
- `--id`：技能 id，只允许字母、数字、下划线、连字符（1–64 位），全局唯一。
- `--name`：显示名称；`--tags`：逗号分隔的标签，用于以后检索（如 `excel,report`）。
- `--entry`：入口命令，如 `"python run.py"`；留空则自动推断脚本。
- `--yes`：直接写入 `manifest.json`；**不加 `--yes` 只预览不写盘**（会打印 manifest 和"加 --yes 写入"提示）。
- 可选：`--description`、`--timeout 120`、`--multiple FIELD`（把某输入/输出字段标记为多值，可重复）。

执行成功后目录里会多出 `manifest.json`，终端打印 `{"manifest": ..., "path": ..., "written": true}`。

> 想交互式逐项确认字段（不写命令行参数），用 `python -m workon init D:/work/my-job`，向导会问 id、名称、标签、入口并让你确认后写入。

### 第 4 步：核对输出声明

`capture` 会按字符串字面量推断 stdout 文本输出与常见相对路径的 file 输出，但推断不一定准确——**务必核对一遍**：缺的补上、多余的删掉、`path` 的 glob 要对得上脚本真实写的位置。

> ⚠️ **一旦你手改过 `manifest.json`，就不要再重跑第 3 步的 `capture`**——它会用自动推断的结果整体覆盖你的手改内容（`description`、`outputs` 都会被重置）。要改就改 manifest，别再 capture。

### 第 5 步：登记目录，让 workon 能发现技能

`capture` 只写 `manifest.json`，还需把该目录登记进技能库（一次即可）：

```bash
python -m workon skill add D:/work/my-job
```

> 若该目录本来就放在内置 `skills/` 下，会自动被发现，可跳过这步。标签已在第 3 步 `--tags` 中登记；如需改标签，重新执行一次 `capture --yes` 覆盖即可。

### 第 6 步：校验（确认固化无误）

```bash
python -m workon skill validate D:/work/my-job   # 传目录，不是 manifest 文件
python -m workon skill list                       # 技能出现在列表中
python -m workon tags                             # 标签已登记
python -m workon skill show my-job                # 查看契约细节
```

`validate` 通过会输出 `{"valid": true, "id": "my-job", "name": "..."}`；`list` 中能看到 id 与标签即表示登记成功。

### 第 7 步：用真实样例跑一次，验证复现

```bash
python -m workon skill run my-job \
  --input text="hello" \
  --file source="./sample_input.xlsx" \
  --param mode="detailed"
```

- `--input KEY=VALUE`：文本或 json 输入；`--file KEY=PATH`：文件输入（可多次）；`--param KEY=VALUE`：运行参数（可多次）；`--json payload.json`：从文件批量读取 inputs/params。
- 返回 JSON 中有 `status`、`outputs`（`stdout` 原始输出、`text`/`json` 具名输出、`files` 输出文件）、`duration_ms`。
- 输出文件会被复制到持久目录 `data/runs/<run_id>/outputs/`，临时工作目录随后被清理，不会丢文件。
- 跑通并与第 2 步确认的结果一致 → 固化完成。**以后文员直接跑第 7 步，AI 退场。**

---

## 2. 给文员的极简日常操作（AI 不在场时）

固化完成后，日常只需两条命令：

```bash
export PYTHONIOENCODING=utf-8
python -m workon skill list                         # 看看有哪些技能
python -m workon skill run my-job --input text="这次的内容"
```

或打开 Web 控制台点选：

```bash
python -m workon serve      # 浏览器访问 http://localhost:8080
```

打开 `http://localhost:8080` 先看到**首页**，点「**进入工作台**」→ 密码登录（默认 `workon`，登录后可在「设置」修改，也可用 `WORKON_PASSWORD` 预设）→ 进入「**召唤技能**」。工作台带 ⭐ 官方徽章的官方能力（PDF 合并/拆分）开箱即用。

在"召唤技能"页选技能、填输入、点击执行即可；结果和下载文件直接显示在页面。

---

## 3. 安装到各个 Agent（一条命令）

`workon/skills/workon-capture/` 本身就是一份符合 [Agent Skills 开放标准](https://agentskills.io/specification)
的 SKILL.md（源文件放在核心包内，pip 安装后也能找到）。workon 自带安装器，把它装进各 Agent 的**用户级** skills 目录：

```bash
python -m workon install-skill --list      # 先看本机装了哪些 Agent、会写到哪里
python -m workon install-skill             # 装到本机已检测到的 Agent
python -m workon install-skill --agent claude --agent codex   # 指定目标
python -m workon install-skill --force     # 覆盖已存在的旧版本
python -m workon uninstall-skill           # 卸载
```

已核对的目录约定（安装器内置，无需你记）：

| Agent | 用户级目录 | 说明 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | 官方文档确认；也支持项目级 `.claude/skills/` |
| Codex CLI / ChatGPT Codex | `~/.agents/skills/<name>/SKILL.md` | 官方用户级位置即通用目录，安装器按目录去重 |
| Qoder | `~/.qoder/skills/<name>/SKILL.md` | 官方文档确认；也读 `~/.agents/skills` |
| 通用标准 | `~/.agents/skills/<name>/SKILL.md` | 跨客户端目录，多款客户端会读 |
| WorkBuddy | `~/.workbuddy/skills/<name>/SKILL.md` | 与 WorkBuddy 现有技能同构 |

安装器会把**本机 workon 项目路径与 Python 解释器**注入 SKILL.md 正文，所以装好后那个 Agent
不需要猜路径。项目换位置或换虚拟环境后，重新跑一次 `install-skill --force`。

> 为什么要单独装：workon 项目代码和 Agent Skill 是两样东西。项目代码是执行引擎，
> Agent Skill 是「说明书」，只有装进 Agent 的 skills 目录，你在 WorkBuddy 里说
> 「把这个工作固化到 workon」时它才会读到。

### 版本与更新检查

两样东西各自有版本号，互不干扰：

- **执行引擎**：`python -m workon --version`（当前包版本，如 `0.4.0`）。
- **技能说明书**：装在 Agent 目录里的 `SKILL.md`，版本号写在其 frontmatter 的
  `metadata.version`（当前技能版本 `1.0.0`）。它被复制过去后就不再跟着项目走，
  项目升级不会自动更新它。

用一条命令同时检查两者是否需要更新（只读，不会改动任何文件）：

```bash
python -m workon update-check                    # 联网检查包 + 各 Agent 里已装技能
python -m workon update-check --agent workbuddy  # 只看某个 Agent
python -m workon update-check --offline          # 断网时只看本机已装技能版本
```

- 提示引擎有新版：`git -C <项目目录> pull` 拉取后重装。
- 提示技能过期：跑一次 `python -m workon install-skill --force` 刷新说明书。

> 本项目**尚未发布到 PyPI**。PyPI 上的 `workon` 是另一个作者的项目，更新检查会
> 自动识别并忽略它，不会引导你 `pip install -U workon` 装错包。请以 GitHub 仓库为准。

---

## 4. 三种 Agent 的触发方式

| Agent | 怎么触发本协议 |
| --- | --- |
| **WorkBuddy** | `python -m workon install-skill --agent workbuddy`；之后说"把这个固化成技能"即自动加载 |
| **Codex / CLI 类 Agent** | `python -m workon install-skill --agent codex`；或在任务说明末尾附本文件并要求"完成后按 workon 固化协议执行" |
| **Qoder / 其他 IDE Agent** | `python -m workon install-skill --agent qoder`（或 `--agent agents` 走通用目录）；也可把第 1、3、4、5、6、7 步作为验收清单写进提示词 |

无论哪种 Agent，都必须遵守第 2 步的人工确认关卡，且不得在固化后自行"优化"脚本——冻结层只负责复现，不负责改动。

---

## 5. 常见问题

- **`capture` 提示 id 非法**：只允许 `[A-Za-z0-9_-]{1,64}`，去掉空格和中文再试。
- **`skill run` 找不到技能**：确认已执行 `skill add <dir>`，或目录在 `skills/` 下；再 `python -m workon skill reload` 重扫一次。
- **占位符没被替换**：`entry.args` 里写 `{字段名}`，名字要和 manifest 的 inputs/params 的 `name` 一致；未提供的占位符会直接报错。
- **多个文件输入传不进去**：把对应字段声明 `multiple: true`，capture 时加 `--multiple 字段名`，运行时用多个 `--file KEY=PATH`。
- **中文乱码**：先设置 `PYTHONIOENCODING=utf-8`（见第 0 节）；runner 本身也默认注入该变量。
- **想删掉技能**：从 `data/settings.json` 的 `skill_dirs` 移除对应目录后 `skill reload`；文件仍在原目录，不会自动删除。

---

## 6. 设计原则（写给 Agent，别违反）

1. **一次确认，永久冻结**：确认后不再调用 AI、不再改脚本。
2. **输入即样例**：固化目录里保留输入样例，便于随时回归验证。
3. **本地优先**：契约、历史、输出全在本机 SQLite 与本地文件，不外传数据。
4. **可复制优先**：命令与目录结构标准化，任何 Agent 照抄即可，不依赖个人经验。
5. **安全边界**：只登记可信来源的脚本；命令受白名单约束，执行在临时目录隔离，超时 3600 秒封顶。
