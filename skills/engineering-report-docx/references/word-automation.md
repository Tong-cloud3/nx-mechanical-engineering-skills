# Word 自动化与排版避坑

## 1. `python-docx` / XML 改稿要点

- **禁止粗暴整段重写含公式或上下标的段落**：直接给 `paragraph.text = ...` 会清空段落内所有 `m:oMath` 公式、图片 `w:drawing`、交叉引用域与上下标格式。改写前先检查段落 XML 是否包含 `oMath`、`drawing`、`fldChar` 或 `vertAlign`，有则按 Run 精准修改。
- **中西文字体必须同时设置**：仅改 `run.font.name` 在中文 Word 中经常只生效西文。应同步设置 `rFonts` 的 `w:ascii`、`w:hAnsi`（如 `Times New Roman`）与 `w:eastAsia`（如 `宋体` 或 `黑体`）。
- **三线表边框**：顶线与底线一般设 `1.5 pt`（`sz="12"`），表头下线设 `0.75 pt`（`sz="6"`），其余内外竖线与数据行横线设 `val="none"`；表头行开启 `w:tblHeader`（跨页重复表头），数据行开启 `w:cantSplit`（防止单行被从中间劈开）。
- **图文防拆分**：图片段落设置 `keep_with_next = True` 绑定下方图注；表题段落设置 `keep_with_next = True` 绑定下方表格；标题段落保持 `keep_with_next = True` 防止标题落在页末。

## 2. Windows Word COM 防卡死与防锁文件

- 批量修改后调用本机 Word 刷新分页/目录并导出 PDF 时：
  - 始终设置 `word.Visible = False` 与 `word.DisplayAlerts = 0`；
  - 始终用 `try ... finally` 确保 `doc.Close(False)` 和 `word.Quit()` 执行；否则异常中断会遗留后台 `WINWORD.EXE` 进程锁死 `.docx`，导致用户随后打开 Word 报错或提示只读/损坏。
  - 刷新分页用 `doc.Repaginate()`，读取总页数用 `doc.ComputeStatistics(2)`，导出 PDF 用 `doc.ExportAsFixedFormat(pdf_path, 17)`。
  - 若 Word COM 因弹窗、字体缺失或卡死长时间无响应，**不要死等**：结束本次脚本启动的会话，改用 LibreOffice 独立 profile 导出：
    ```text
    "C:\Program Files\LibreOffice\program\soffice.com" -env:UserInstallation=file:///绝对临时目录/lo_profile --headless --nologo --norestore --convert-to pdf --outdir 输出目录 输入.docx
    ```
    （注意：LibreOffice 的分页与 Microsoft Word 偶有 1 页以内偏差，最终打印/交稿前的目录页码核对仍以 Word 分页为准。）

## 3. 交付前肉眼复核清单

1. **目录与页码**：目录点线、缩进、页码右对齐是否整齐，各章首页页码是否与目录完全一致。
2. **图表与编号**：`图X-Y`、`表X-Y` 无跳号、无重号、正文引用全匹配；云图色标数值、坐标轴、尺寸标注放大后可辨认。
3. **分页与版面**：无标题落单、无图与图注分居两页、无表头与首行断开、无大块异常留白或末页只剩一两行。
4. **隐私与模板留空**：封面、任务书、调查表未误填他人姓名/学号或遗留“模板示例课题名称”。
