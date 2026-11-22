---
name: workon-capture
description: 把 AI 刚完成的一次性工作固化成 workon 技能。当用户说“保存成技能”“固化这个工作”“以后不用再调 AI 直接跑”“这活以后点一下就复现”“把这个脚本登记为技能”“召唤技能/复现固定工作”等，或用户已确认某段脚本/目录的结果正确、希望留存供以后反复使用时触发。也用于指导创建 input/output/params 契约、打标签、验证技能可运行。
---

# workon-capture：把一次工作冻结成确定性技能

你是 AI Agent。workon 是「AI 产出的冻结层」：用户认可你这次的产出后，把它固化成本地脚本技能，以后**不再调用 AI**，文员点一下就确定性地复现。你的任务是把一次已完成并确认的工作，按下面步骤固化成合规的 workon 技能。

## 核心原则

- **先确认再固化**：用户没明确认可结果前，不要写 `manifest.json`。确认是唯一的人工关卡。
- **冻结即不再改**：固化完成后不要"顺手优化"脚本；复现靠同一份文件，不靠再生成。
- **本地优先**：只用 workon CLI 与本地文件，契约和历史都在本机 SQLite，不外传数据。
- **命令怎么跑**：本文所有命令形如 `{{WORKON}} skill list`。`{{WORKON}}` 是本机 workon 的
  启动器路径，**在你读到的这份已安装文件里已经是可直接执行的真实路径**——原样复制即可，
  不要自己改写成 `python -m workon`（那会报 `No module named workon`）。若你看到的仍是字面的
  `{{WORKON}}`（说明这是未安装的源文件），改用 `python -m workon` 并在 workon 项目根目录下执行。
- **终端编码**：启动器已内置 UTF-8；若你绕过启动器自己调用，先设
  `PYTHONIOENCODING=utf-8`（Bash: `export PYTHONIOENCODING=utf-8`；PowerShell:
  `$env:PYTHONIOENCODING = "utf-8"`；cmd: `set PYTHONIOENCODING=utf-8`）。

## 步骤

### 1. 收敛产物到一个目录
确认工作已真正完成且验证正确。把以下内容放进同一个目录（下称 `<dir>`，尽量用绝对路径）：
- 能**非交互**运行的主脚本（所有输入走命令行参数或固定路径，不要 `input()`、不要弹窗）；
- 它依赖的其他脚本、模板文件（子目录会被一并复制，`lib/`、`templates/` 都支持）；
- 一个输入样例（便于以后回归验证）；
- 可选 `requirements.txt`（脚本自身的依赖说明）。

输出应写到当前工作目录或由参数指定路径——workon 每次在临时目录执行脚本。不要放入真实敏感业务数据。

#### 输出路径：写到相对路径，别让用户传绝对路径

这是最容易做错的一步。**让脚本把结果写到相对当前目录的路径**（如 `out/summary.txt`），
manifest 里用 `path` 声明它，workon 会自动收集并持久化到 `data/runs/<run_id>/outputs/`。

反例（错误做法，会让技能难用）：

```python
p.add_argument("--out", required=True)   # 文员被迫手填一个绝对路径
```

这样 capture 会把 `--out` 推断成一个 **text 输入**，文员每次召唤都得自己想一个输出路径，
而且 workon 不会把结果收进 `outputs.files`，等于丢掉了"固定输出"这个核心价值。

正例：

```python
from pathlib import Path
Path("out").mkdir(exist_ok=True)
Path("out/summary.txt").write_text(result, encoding="utf-8")
```

manifest 的输出声明：

```json
"outputs": [
  { "name": "summary", "type": "file", "path": "out/*.txt", "multiple": true }
]
```

规则小结：
- 只要产生文件，就用**相对路径**写盘 + `outputs[].path` 声明（支持 `glob` 通配）；
- 纯文本结果直接 `print()`，capture 会自动生成 `source: "stdout"` 的 text 输出；
- 需要从 stdout 的 JSON 里取某个值，用 `type: "text"` + `json_key`（**不是** `type: "json"`，
  `json` 类型只从落盘文件读）。

### 2. 人工确认（强制）
向用户展示：脚本做什么、输入输出是什么、这次跑出来的结果。等用户明确说"确认/可以/保存"再继续。不要跳过。

### 3. 生成 manifest 并固化
用 capture 扫描目录自动生成 `manifest.json`。`--yes` 表示非交互直接写入：

```
{{WORKON}} capture "<dir>" --id <唯一id> --name "显示名称" --tags tag1,tag2 --entry "python run.py" --yes
```

- `<dir>`：第 1 步的目录；`--id`：仅字母/数字/下划线/连字符，1–64 位，全局唯一；
- `--tags`：逗号分隔，登记技能标签；`--entry`：入口命令，留空自动推断脚本；
- 可选 `--description`、`--timeout 120`；`--multiple 字段名`（多值字段，可重复）；
- 不加 `--yes` 时**只预览不写盘**，会提示加 `--yes` 固化。
- 想要交互式逐项确认，改用 `{{WORKON}} init "<dir>"`，按提示填写并确认。

成功后目录里出现 `manifest.json`，终端打印 `{"manifest":..., "written": true}`。

### 4. 核对输出声明
capture 会静态推断 stdout 文本输出，常见相对路径也会推成 file 输出，但推断是按字符串字面量猜的，
**务必核对一遍**：缺的补上、多余的删掉、`path` 的 glob 要对得上脚本真实写的位置。

> ⚠️ **一旦你手改过 `manifest.json`，就不要再重跑第 3 步的 capture**——实测它会用自动推断
> 的结果整体覆盖你的手改内容（`description`、`outputs` 都会被重置）。要改就改 manifest，
> 别再 capture。

### 5. 登记技能目录
capture 只写 manifest，还要让 workon 发现它（一次即可）：

```
{{WORKON}} skill add "<dir>"
```

如果 `<dir>` 本就在内置 `skills/` 下会自动被发现，可跳过。标签已在第 3 步写入 manifest，无需单独登记标签。
（Web 网页里新登记的技能需点一次"重新加载"或重启进程才会出现；命令行每次启动都会重新扫描。）

### 6. 校验契约

```
{{WORKON}} skill validate "<dir>"
```
```
{{WORKON}} skill list
```
```
{{WORKON}} tags
```

`validate` 输出 `{"valid": true, ...}`、`list` 能看到 id 与标签，才算固化成功。

### 7. 用样例跑一次验证复现

```
{{WORKON}} skill run <id> --file src="<样例文件的绝对路径>"
```

- `--input KEY=VALUE` 文本/json 输入；`--file KEY=PATH` 文件输入（可多次）；`--param KEY=VALUE` 参数（可多次）；`--json FILE` 批量读取。
- **`--file` 给绝对路径**：相对路径是按你当前 shell 的工作目录解析的，不是按技能目录，很容易"输入文件不存在"。
- 检查返回的 `status` 是否为 `success`、`outputs.stdout`/`outputs.text`/`outputs.files` 是否与第 2 步确认的结果一致。
- 输出文件已持久化到 `data/runs/<run_id>/outputs/`，临时目录会被清理，不会丢失。
- 跑通且结果一致 → 固化完成。之后把这个技能的使用方式交给用户，你（AI）退场。

## 完整范例：把"CSV 汇总"固化成一个技能

用户的场景：AI 刚帮他写了个脚本，把业务 CSV 汇总成报表。确认结果正确后要固化。

**（对应第 1 步）在工作目录放好脚本和样例**

```
D:\work\csv-sum\
├── run.py            # 主脚本，非交互
├── sample.csv        # 输入样例
└── requirements.txt  # 可选
```

`run.py`（注意输出写到相对路径 `out/`，不是让用户传 `--out`）：

```python
import argparse, csv
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--src", required=True, help="输入 CSV")
args = p.parse_args()

rows = list(csv.DictReader(open(args.src, encoding="utf-8-sig")))
total = sum(float(r.get("amount") or 0) for r in rows)

Path("out").mkdir(exist_ok=True)
Path("out/summary.txt").write_text(
    f"rows={len(rows)}\ntotal={total:.2f}\n", encoding="utf-8"
)
print(f"rows={len(rows)} total={total:.2f}")   # 会被收成 text 输出
```

**（对应第 2 步）向用户确认**（强制，不可跳过）

> "这个脚本读一个 CSV，输出 out/summary.txt（行数+金额合计）。刚才跑出来 rows=3 total=33.50。
> 确认保存成技能吗？"

**（对应第 3 步）生成 manifest 并固化**

```
{{WORKON}} capture "D:\work\csv-sum" --id csv-sum --name "CSV金额汇总" --tags excel,report --entry "python run.py --src {src}" --yes
```

**（对应第 4 步）核对输出声明**

编辑生成的 `manifest.json`，把 `outputs` 改成：

```json
"outputs": [
  { "name": "result", "type": "text", "source": "stdout" },
  { "name": "summary", "type": "file", "path": "out/summary.txt", "required": false }
]
```

**（对应第 5 步）登记**

```
{{WORKON}} skill add "D:\work\csv-sum"
```

**（对应第 6 步）校验**

```
{{WORKON}} skill validate "D:\work\csv-sum"
```

**（对应第 7 步）试用**

```
{{WORKON}} skill run csv-sum --file src="D:\work\csv-sum\sample.csv"
```

期望返回 `status: "success"`，且 `outputs.files` 里有 `summary.txt` 指向
`data/runs/<run_id>/outputs/summary.txt`。这表示文员以后只要给一个 CSV，点一下就出报表。

**交给用户，你退场**

告诉用户：「技能 `csv-sum` 已固化。以后把 CSV 拖进 workon 网页选这个技能，或者命令行跑
`{{WORKON}} skill run csv-sum --file src=你的文件.csv`。不再需要 AI。」

## 契约速查

- 输入类型：`text` / `file` / `docx` / `xlsx` / `json` / `image` / `dir`；输出类型：`text` / `file` / `docx` / `xlsx` / `json` / `dir`。
- 字段可加 `multiple: true` 表示多值；`entry.args` 用 `{字段名}` 占位符引用输入/参数；内置 `{workdir}` `{skill_dir}` `{run_id}`。
- 整条 arg 是占位符时，多值路径会被分词展开成多个参数；嵌入形式（如 `--files={files}`）保持单个参数。
- params 类型 `string` / `number` / `boolean`；布尔参数可配 `flag`（为 true 时追加命令行 flag）。
- timeout 上限 3600 秒；命令必须在白名单内（`python` 会自动用当前解释器）。

## 失败处理

- id 非法 → 改用 `[A-Za-z0-9_-]{1,64}`。
- 找不到技能 / 命令报 `No module named workon` → 用本文命令里的 `{{WORKON}}` 启动器，
  再 `{{WORKON}} skill reload`。
- 占位符没替换 → 核对 `entry.args` 的 `{名}` 与 manifest 中 inputs/params 的 `name` 完全一致。
- 多文件传不进 → 对应字段声明 `multiple: true`（capture 加 `--multiple 字段名`）。
- 脚本里 import 自己的子模块失败 → 确认子目录（`lib/`）和第 1 步放在同一目录下，workon 会递归复制。
- 中文乱码 → 用 `{{WORKON}}` 启动器（已内置 UTF-8），或自己设 `PYTHONIOENCODING=utf-8`。

## 关于版本与更新

- 本技能文件由 workon 安装器生成，frontmatter 的 `metadata.version` 是它的版本号。
- 想确认是否需要升级：跑 `workon update-check`（或 `python -m workon update-check`），
  它会对比 PyPI/GitHub 上的最新版本与本机版本，并列出各 Agent 目录里已安装技能的版本差异。

完整人工协议见仓库根目录 `AGENT-GUIDE.md`；manifest 全字段见 `docs/skill-format.md`。
