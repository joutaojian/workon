# 文本回显（text-echo）

最小技能示例：输入一段文字，输出处理后的文字。

## 召唤

```bash
python -m workon skill run text-echo --input text="hello workon" --param upper=true
```

Web 界面中在「召唤技能」页选择本技能，填写文本并点击召唤即可。

## 说明

- manifest 中 `entry.command` 为 `python`，runner 会自动替换为当前解释器。
- `{text}` 占位符在运行时被输入值替换。
- 布尔参数 `upper` 为 true 时，runner 会追加 `--upper` flag。
- 输出 `result` 未声明 `json_key`，因此脚本的标准输出（去掉首尾空白）直接作为该文本输出返回。
