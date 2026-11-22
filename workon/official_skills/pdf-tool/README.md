# PDF 合并与拆分（官方）

免费替代 WPS 付费功能：把多个 PDF 合并成一个，或把一个 PDF 按页码拆成多个单页 PDF。纯 Python 标准库实现，不联网、不装依赖。

## 用法

在网页工作台「召唤技能」里选 **PDF 合并与拆分**：

- 上传一个或多个 PDF（`files`，可多选）
- `mode`：`merge`（合并，默认）或 `split`（拆分）
- `pages`：仅拆分模式有效，页码范围如 `1-3,5,7-9`；留空拆全部页面

命令行等价写法：

```bash
# 合并：多个 PDF → merged.pdf
python -m workon skill run pdf-tool --file files=a.pdf --file files=b.pdf

# 拆分：一个 PDF 拆成单页，输出到 split_pages/ 目录
python -m workon skill run pdf-tool --file files=a.pdf --param mode=split --param pages=1-3
```

## 输出

- 合并：`merged.pdf`
- 拆分：`split_pages/` 目录，每页一个 PDF（`page_0001.pdf`、`page_0002.pdf` …）

输出文件名是对外契约，请勿修改。本技能为官方内置能力，不可删除或改 id。
