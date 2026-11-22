# 技能格式规范（manifest.json）· v0.2

一个技能就是一个目录，核心是 `manifest.json`，外加执行脚本与依赖文件。

```
my-skill/
  manifest.json     # 必需：技能契约
  run.py            # 入口脚本（语言由 entry.command 决定）
  README.md         # 可选：说明
  requirements.txt  # 可选：技能自身依赖
  sample_input.*    # 可选：输入样例，便于回归验证
```

固化技能不要手写 manifest：用 `python -m workon capture <dir> --id <id> --yes` 扫描目录自动生成，或 `python -m workon init <dir>` 交互式生成。AI Agent 的固化协议见仓库根目录 `AGENT-GUIDE.md`。

## manifest.json 字段

| 字段 | 类型 | 必需 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 全局唯一标识，正则 `[A-Za-z0-9_-]{1,64}` |
| `name` | string | 否 | 显示名称，默认用 id |
| `description` | string | 否 | 技能描述 |
| `version` | string | 否 | 版本，默认 `0.1.0` |
| `author` | string | 否 | 作者 |
| `tags` | string[] | 否 | 标签，用于分类与检索 |
| `inputs` | object[] | 否 | 输入字段声明，见下表 |
| `outputs` | object[] | 否 | 输出字段声明，见下表 |
| `params` | object[] | 否 | 运行参数声明 |
| `entry` | object | 是 | `{"command": "...", "args": [...]}` |
| `timeout_seconds` | number | 否 | 超时秒数，默认 120，上限 3600 |
| `dependencies` | string[] | 否 | 依赖说明（仅作文档用途） |

### inputs / outputs 字段

| 字段 | 说明 |
| --- | --- |
| `name` | 字段标识；同时作为 `entry.args` 中的 `{占位符}` 名 |
| `type` | 见下方类型表；inputs 与 outputs 允许的类型略有差异 |
| `required` | 是否必填，默认 `true` |
| `description` | 说明 |
| `ext` | 允许的文件扩展名数组（如 `["csv","txt"]`），对 `docx`/`xlsx` 会额外校验扩展名 |
| `source` | 文本来源标注（默认 `stdout`），供人阅读与 capture 推断使用；执行器实际取 stdout，提取规则见 `json_key` |
| `path` | 输出文件路径或 glob（如 `output.xlsx`、`result/*.json`），支持 `{workdir}` |
| `json_key` | 文本输出：从 stdout 的 JSON 中按点分路径提取文本（如 `data.result`）；未声明时取完整 stdout |
| `multiple` | 布尔值，默认 `false`；为 `true` 时该字段接受/返回多个值，见下方「多值字段」 |

**类型表（v0.2 新增 `json` / `image` / `dir`）**

| 类型 | 可作输入 | 可作输出 | 运行时行为 |
| --- | --- | --- | --- |
| `text` | ✅ | ✅ | 数据型输入直接作为字符串注入占位符；输出为文本（stdout 或 `json_key` 提取） |
| `json` | ✅ | ✅ | 输入数据序列化为 `<字段名>.json` 落盘并注入路径；输出文件会被解析为 JSON 对象放入 `outputs.json`，单值自动解包、多值为列表 |
| `file` | ✅ | ✅ | 任意文件，复制到临时工作目录，占位符替换为落盘路径 |
| `image` | ✅ | ❌ | 图片文件，行为同 `file`（按扩展名落盘） |
| `docx` | ✅ | ✅ | Word 文件，校验 `.docx` 扩展名后落盘 |
| `xlsx` | ✅ | ✅ | Excel 文件，校验 `.xlsx` 扩展名后落盘 |
| `dir` | ✅ | ✅ | 目录输入整棵复制进工作目录；目录输出收集后持久化（见输出持久化） |

> 注意：`image` 只能作输入，不能作输出；`dir` 输出以目录形式持久化。

### params 字段

| 字段 | 说明 |
| --- | --- |
| `name` | 参数名；可作为 `{占位符}` 使用 |
| `type` | `string` / `number` / `boolean` |
| `default` | 默认值（boolean 默认 `false`，其余默认空串） |
| `flag` | 布尔参数为 true 时追加的命令行 flag（如 `--upper`）；声明后该参数只通过 flag 传递，不进入占位符 |
| `choices` | 可选值列表，传入其他值会报错 |
| `description` | 说明 |

## 占位符与执行

- `entry.args` 中的 `{字段名}` 在运行时被输入值或参数值替换；引用未提供的占位符会**直接报错**，不会静默留空。
- 内置可用占位符：`{workdir}`（临时工作目录）、`{skill_dir}`（技能原目录）、`{run_id}`（本次执行 id）。三者由执行器注入，无需在 inputs/params 中声明。
- 文件/目录/json 输入会被落盘到临时工作目录，占位符替换为**落盘后的路径**。`text` 输入直接替换为文本值。
- `entry.command` 为 `python`/`python3` 时自动替换为当前 Python 解释器；命令的第一个 token 必须在白名单内（默认：`python`、`python3`、`node`、`bash`、`sh`、`powershell`、`pwsh`，可用 `WORKON_ALLOWED_COMMANDS` 覆盖）。
- 技能目录中的脚本文件在执行前被复制到临时工作目录，因此可用相对路径引用；`manifest.json`、`README.md`、`settings.json` 不会被复制。
- 子进程环境变量包含 `WORKON_RUN_ID`、`WORKON_WORKDIR`，并默认设置 `PYTHONIOENCODING=utf-8`。

### 占位符分词规则（v0.2）

多值字段（`multiple: true`）落盘后是一串**带引号的路径列表**。分词规则：

- **仅当整条 arg 本身就是一个占位符**（如 `args: ["{files}"]`）时，执行器才把替换后的路径串按空格分词，展开成多个命令行参数（引号内的路径含空格也不拆开）。
- 若占位符嵌在更大的字符串里（如 `"--files={files}"`、`"prefix-{files}"`），则**保持为单个参数**，不做分词。
- 单值字段永远是把落盘路径作为一个参数传入，不分词。

示例：`args: ["run.py", "--inputs", "{files}"]` 且 `files` 是多值字段时，实际命令为 `python run.py --inputs "a.xlsx" "b.xlsx"`（两个路径是两个参数）。

## 多值字段（multiple）

- 声明 `"multiple": true` 后：
  - 输入：可传一个列表（CLI 多次 `--file KEY=PATH` / `--input KEY=VALUE`，Web 多文件上传）；每项独立走校验和落盘。
  - 输出：收集所有匹配 `path`/glob 的文件（或目录），全部进入结果与持久化目录；`json` 输出为列表。
- 单值字段若收到数组会被拒绝（避免静默只取第一个）。
- `capture` 时可用 `--multiple 字段名`（可重复）强制把推断出的字段标记为多值。

## 输出与持久化

执行器在子进程结束后收集输出，返回结构：

```
outputs:
  stdout    str                       原始标准输出（截断到 20000 字符）
  stderr    str（可选）                标准错误
  text      {name: value}             具名文本输出：json_key 提取值，否则完整 stdout
  json      {name: obj | list}        类型为 json 的输出文件内容（单值解包、多值列表）
  files     [{name, filename, path, size, type, persisted, is_dir?}]  文件/目录输出
  returncode int                      脚本退出码
```

**输出持久化（v0.2）**：临时工作目录在每次执行后会被删除。为避免文件输出丢失，执行器会把 `files` 中的文件/目录复制到持久目录 `data/runs/<run_id>/outputs/`，并在每个条目上标记 `"persisted": true`、`path` 更新为持久路径。文本与 json 输出直接内嵌在结果里，不落盘为文件。已落盘的输入文件不会被误当成输出返回。

## 完整示例

编写完成后可校验技能目录是否合法：

```bash
python -m workon skill validate ./my-skill    # 传入技能目录，不是 manifest 文件
```

完整示例见 `skills/text-echo/`。一个处理多个 Excel 的技能可这样声明：

```json
{
  "id": "report-builder",
  "name": "报表生成器",
  "tags": ["excel", "report"],
  "inputs": [
    {"name": "sources", "type": "xlsx", "required": true, "multiple": true, "description": "源数据表（可多份）"},
    {"name": "options", "type": "json", "required": false, "description": "可选配置"}
  ],
  "outputs": [
    {"name": "report", "type": "xlsx", "path": "report.xlsx"},
    {"name": "summary", "type": "text", "json_key": "data.summary"}
  ],
  "params": [
    {"name": "title", "type": "string", "default": "月度报表"},
    {"name": "verbose", "type": "boolean", "default": false, "flag": "--verbose"}
  ],
  "entry": {"command": "python", "args": ["build.py", "{sources}", "--title", "{title}"]},
  "timeout_seconds": 120
}
```

对应召唤命令：

```bash
python -m workon skill run report-builder \
  --file sources="./a.xlsx" --file sources="./b.xlsx" \
  --param title="九月报表" --param verbose=true
```
