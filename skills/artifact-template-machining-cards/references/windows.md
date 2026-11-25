# Windows本机工具链

本节是本机可用路径，不将其写入通用工艺要求。其它机器先检测工具，再选入口。

- AutoCAD 2023控制台：`C:/Program Files/Autodesk/AutoCAD 2023/accoreconsole.exe`。可用`/i 输入DWG /s 脚本.scr`，或SCR加载LISP批量绘图。脚本中先设置输出目录，避免覆盖输入DWG。中文SCR/LISP按本机控制台兼容编码处理；本机CP936可用。
- LibreOffice：`C:/Program Files/LibreOffice/program/soffice.com`。使用任务目录下独立profile：`-env:UserInstallation=file:///绝对路径/profile --headless --nologo --norestore --convert-to pdf --outdir 输出目录 输入.docx`。优先以subprocess参数列表传递中文路径。
- DOCX可通过zipfile+XML精确改表，不依赖Word COM。保留关系、图像、命名空间与mc:Ignorable声明；只序列化改动的document/styles等部件，其他部件原字节保留。原始样例纸张是A4横向，保留在本技能的reference.docx已按比例转为A3横向；不要再次乘√2。
- PDF 导出与逐页审图：
  - **LibreOffice 独立 profile（批量导出首选，避免交互阻塞）**：见上文 `soffice.com` 命令。
  - **本机 Word COM（需要核对 Word 原生分页/目录页码时使用）**：通过 `win32com.client.Dispatch("Word.Application")` 调用，必须设置 `word.Visible = False`、`word.DisplayAlerts = 0` 并在 `try...finally` 中关闭文档并执行 `word.Quit()`，防止残留僵尸 `WINWORD.EXE` 锁死 `.docx` 导致后续打开报错；分页核对用 `doc.Repaginate()` + `doc.ComputeStatistics(2)`，导出 PDF 用 `doc.ExportAsFixedFormat(pdf_path, 17)`。若 COM 出现阻塞或弹窗卡住，立即中止并回退 LibreOffice，不要长时间死等。
  - **页面转图核查**：直接使用本技能自带 `scripts/windows_pdfium.py 输入.pdf 输出目录 --width 2400`，利用本机 LibreOffice 的 `pdfiumlo.dll` 生成高清页面图（需 Pillow）；不能只统计页数而不看图。
- `sheetgen.py`是可选图元库。新图按实际零件编写Sheet内容，使用build_lisp生成图形，再由控制台执行。它的图纸输出为A4工序图，插入的工艺卡仍为A3。默认不包含学校名称。
