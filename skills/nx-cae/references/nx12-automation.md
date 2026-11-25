# NX 12 CAE 自动化与原生后处理截图（本机实测模式）

本节汇总 Siemens NX 12（`<NX_INSTALL_DIR>`，如 `C:\Program Files\Siemens\NX 12.0`）已验证的 NXOpen 批处理与原生后处理截图链路。API 名称随版本可能不同；在其它环境使用前先核查安装路径与接口。

## 1. 模态方案（SOL 103）批处理修复与结果绑定

新建 SOL 103 方案不会自动继承静力学约束，且容易出现空壳方案、复用静力输出请求导致 `.op2` 暴涨、或 `ResultReference` 路径/单位错配。推荐按以下顺序用 `NXBIN\run_journal.exe` 处理：

1. **完整加载与切换目录**：先设置 `s.Parts.LoadOptions.UsePartialLoading = False` 并 `os.chdir(work_dir)`，再 `OpenBaseDisplay(sim_path)`。
2. **同步约束**：读取对应静力方案的 `ssol.GetBcs()`（若为空则核对 `sim.Constraints`），逐项通过 `msol.AddBc(bc)` 挂到模态方案，避免漏约束算出 `~0.0006–0.0009 Hz` 的刚体自由模态。
3. **补齐 Lanczos（`EIGRL`）**：检查 `msol.PropertyTable.GetNamedPropertyTablePropertyValue("Lanczos Method")`。缺失时复用或创建 `Real Eigenvalue - Lanczos` 属性表，配置 `ND`（如 `10`）、`MAXSET=7`、`NORM=0`（质量归一化）并挂回 `msol.PropertyTable`。
4. **拆分独立输出请求（防 `.op2`/`.f06` 暴涨）**：
   - 切勿直接修改静力学方案共用的 `Output Requests` 对象；
   - 通过 `part.ModelingObjectPropertyTables.CopyModelingObjectPropertyTable(or_static)` 复制出独立的 `Modal Output Requests1`；
   - 开启 `Displacement - Enable` 与 `Effective Mass - Enable`，关闭 `Stress - Enable` 与 `SPC Forces - Enable`，再绑定到 `msol`（实测可将单件模态 `.op2` 从 `~610 MB` 降至 `~155 MB`）。
5. **绑定本地结果路径与一致单位制**：
   - 取静力方案单位 `static_units = ssol.GetResultReferenceByIndex(0).GetResultFileUnits()`；
   - 对模态结果引用调用 `mref.SetLocalResultFile(work_dir, op2_name)` 和 `mref.SetResultFileUnits(static_units)`，防止 `Tonne` 与 `Kilogram` 混用或结果路径失效。
6. **导出、求解与独立重开核验**：
   - `msol.Solve(SolveOption.WriteSolverInputFile, SetupCheckOption.DoNotCheck)` 导出 `.dat`；
   - 用 `nxnastran\bin\nastran.exe <dat> prog=bundle old=no scratch=yes` 后台求解，交叉检查 `.log` 中 `Normal modes analysis completed` 与 `Analysis complete  0`；
   - 求解结束后在**新会话**重开 `.sim`，再次确认 `SetLocalResultFile` / `SetResultFileUnits`，用 `s.ResultManager.CreateSolutionResult(msol)` 校验节点数、单元数和各阶 `Loadcase/Iteration` 频率值可读，最后保存 `.sim`。

## 2. NX 12 原生后处理云图自动截图

当用户要求“与 NX 软件界面一致的真实后处理截图”时，**不得**用 matplotlib/PyVista 自绘伪造云图。`run_journal.exe` 无图形界面，无法直接渲染云图，需通过真实 GUI 会话抓取 OpenGL 帧缓冲：

1. **启动与触发时机（关键）**：
   - 设置隔离的 `UGII_USER_DIR`（含 `startup\auto_capture.py`）和 `UGII_CAE_POST_TEMPLATE_USER_DIR`；
   - 在 `startup()` 中调用 `SetProcessDpiAwareness(2)`，注册 `s.Parts.AddPartOpenedHandler(on_part_opened)`；
   - 用 `UGII\ugraf.exe -retrieve:<first.sim>` 启动，待首个 `on_part_opened` 写入就绪标志并等待数秒（让 `UG_APP_SFEM` 与 OpenGL 窗口就绪）后，再调用 `NXBIN\ugs_router.exe -ug -use_file_dir <trigger.sim>` 触发主截图逻辑，避免在 `UG_APP_NOPART` 阶段找不到 OpenGL 上下文。
2. **视图与后处理状态设置**：
   - 确认 `s.ApplicationSwitchImmediate("UG_APP_SFEM")`，最大化主窗口并按参考视图方向调整 `ModelingViews.FindObject("SIM_1")`（`Orient` / `Fit` / `SetRotationTranslationScale`）；
   - 加载并创建后处理视图：`res_id = s.Post.LoadSolutionResult(msol)` → `pvid = s.Post.CreatePostview(0, res_id, False)`；
   - 设置变形与边面风格：`PostviewSetDeformed(pvid, True)`、`PostviewSetEdgeFace(pvid, pef, uef)`；
   - 逐阶切换：`PostviewSetShowHeader(pvid, Automatic)` → 选择 `Quantity.Displacement`、`Component.Magnitude` → `PostviewSetResult` → `PostviewUpdate`；如需规范左上角标题，可用 `PostviewExportTemplate` 读取默认行并 `PostviewSetHeaderlines` 自定义第 1 行为 `<part_leaf> : <sol_name>`。
3. **无损帧缓冲抓取与退出**：
   - 调用 `user32.RedrawWindow` + Win32 消息泵（`PeekMessageW` / `DispatchMessageW`）刷新视图；
   - 通过 `opengl32` 校验 `wglGetCurrentContext()`、读取 `GL_VIEWPORT`、`glFinish()`、`glReadBuffer(GL_FRONT)`、`glReadPixels(..., GL_RGB, GL_UNSIGNED_BYTE)` 写出原始 RGB，再用 Pillow 垂直翻转（`FLIP_TOP_BOTTOM`）保存为无损 PNG；
   - 每件截完后执行 `PostviewDelete(pvid)` 与 `UnloadResult(res_id)` 释放显存/内存；全部完成后关闭模型并退出临时 `ugraf` 进程（仅结束本次脚本启动的会话，不误杀用户已有 NX 窗口）。

## 3. 工程瘦身与大文件控制

CAE 工程体积主要来自 `.op2`（二进制结果）和 `.f06`（文本结果）：

| 文件类型 | 用途 | 清理原则 |
| --- | --- | --- |
| `.sim` / `.fem` / `.prt` | 模型、网格与仿真定义 | **必须保留** |
| 当前绑定方案的 `.op2` | NX 打开 `.sim` 直接加载云图依赖 | **不能删**；删后打开软件看不到结果 |
| `.f06` | 固有频率、有效质量、应力等文本一手依据 | 建议保留；排查是否误开全节点 `PRINT` 导致异常膨胀 |
| `.dat` | 独立求解输入与物理工况复核依据 | 可由 `.sim` 重新导出；仅在用户明确要求瘦身时再清理 |
| `.f04` / `.log` / `.diag` | 求解过程日志与诊断 | 体积很小，核验存档保留或按用户确认清理 |

从源头控体积最有效的做法是：**模态分析关闭 Stress / SPC Forces 输出请求，且不在高密度网格上滥开文本 `PRINT` 全量输出**。
