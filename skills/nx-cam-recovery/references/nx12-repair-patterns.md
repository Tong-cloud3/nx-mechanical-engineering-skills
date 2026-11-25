# NX12 repair patterns

These patterns came from actual NX12 JXS recovery. Confirm the corresponding installed API before reusing them; dimensions, transforms, paths and tolerances below are examples, not defaults for other parts.

## Load warnings and component references

Capture `PartLoadStatus.NumberUnloadedParts`, `GetPartName(i)`, `GetStatus(i)` and `GetStatusDescription(i)` immediately after `Parts.OpenBaseDisplay`, before `Dispose()`. A successful open can still return unloaded components. An acceptance flag that checks only toolpaths and IPW misses this failure.

A missing `ROLL_*.prt` assembly occurrence can be a temporary visualization component rather than the CAM parameterized tool itself. Establish this distinction before removal. In the observed repair, removing four stale occurrences with `ComponentAssembly.RemoveComponent` preserved all 17 operation names, path lengths and tool-group assignments, and both active turning tools' number, insert size, nose radius, orientation and holder angle. Reopen then reported zero unloaded components. This does not authorize removing genuine model, fixture, holder or machine dependencies.

For required external components, repair/rebuild their references and include them in the delivery. Check the formal delivery directory itself; a test directory or an already-loaded session can accidentally resolve references that the user's fresh session cannot.

## Native IPW versus embedded stage stock

Trace program order and geometry independently. Moving operations into one program group does not merge their workpieces. A child MCS under a workpiece using an old exported stock may keep reading that frozen stock after the program folders are merged.

For native handoff, work from a copy and test moving the relevant setup MCS/operations into the intended common workpiece while preserving their coordinate systems. Recompute sequentially, inspect input/output state, then reopen. Different hierarchy arrangements can alter coordinate inheritance or fail; this is a tested option, not a blanket instruction to flatten every tree.

A useful dynamic test is to move the first downstream operation before its upstream cuts in an isolated copy, regenerate and read input IPW, then restore and repeat. In the 04 case, the first drill input changed from approximately 672102 to 874752 mm³ and returned to approximately 672101 mm³. Use a tolerance appropriate to faceting; these values and a 1 mm³ comparison tolerance are specific evidence, not universal thresholds. Keep the experimental reorder out of the formal part.

`Show3dWorkpiece()` returning does not prove persistence. Null sources, `UnableToUpdate`, or empty geometry contents require further evidence. A validated embedded stock is useful for a physical transfer between machines, but report its frozen nature and how upstream edits require its update. Successful native handoff for one part does not establish it for another.

## Turning IPW coordinate persistence

The local `uf_turn.h` documents `UF_TURN_save_spinning_ipw_as_part` as the workpiece immediately **after** the referenced operation. Verify that the exported PRT contains a valid solid; file existence and size are insufficient. NX12 wrappers sometimes raised `returned NULL without setting an error` despite producing a file; inspect the file and native return status before interpreting that message.

A turning spinning solid may be exported in spindle coordinates, while the design and milling setup use another frame. Inspect axes and bounding boxes before deriving a transform. In the 10 case, mapping raw X axial coordinates to design Z required a cyclic transform. The reliable sequence was:

1. Apply the verified transform through the installed native API.
2. Save, close and reopen the transformed stock.
3. Check its bounding box and orientation, then export/import the verified state for the next setup.

Immediate reads/exports had retained stale coordinates in this case. A zero return from the transform was insufficient. Do not infer from this observation that a particular Python wrapper always fails or that the same transform applies to all NX files.

For a native C call, read the local header, use matching tag/pointer/array types, check return values, and preserve raw errors. A PRT containing no solid after `Failed to create a Revolve feature` is not a valid IPW result. Preserve useful error codes and syslog context instead of hiding the exception.

## Tool factories and planar floor definition

NX12 has specialized builder factories. Inspect `NCGroupCollection` and the local template's actual tools/operations before guessing names.

- A native `T_CUTTER` uses `CreateTToolBuilder`, not the generic `CreateMillToolBuilder`. The generic builder accepted apparently positive scalar values but failed commit with `Diameter must be greater than zero` in the observed case.
- Other specialized tools have their own factories, such as `CreateGrooveToolBuilder`; check the current API rather than assuming that the turning builder handles every insert.
- For the successful planar-profile T-slot operation, define the boundary plane and `builder.Geometry.FloorPlane` explicitly, and select `builder.CutLevel.Types.FloorOnly`. Setting the boundary plane alone still produced no path. A zero constant depth with no usable floor also produced no path.

Validate the committed tool geometry and native operation, not just builder readbacks. Do not silently fall back to an unknown template subtype.

## Undercut example and removal checks

The 10 case had a Ø65 opening and a Ø66.5 internal relief at Z=-79 to -82. The authorized solution used a Ø16 T-head, 3 mm thickness, Ø10 neck and 120 mm overall length. At Z=-82, a tool-center radius of 25.25 gives an outer cutting radius of 33.25; the neck envelope reaches 30.25, leaving 2.25 mm radial clearance to the opening. Entry/retract centers near radius 22.25 keep the head envelope at 30.25 before axial movement. Check the complete motion, upper/lower lips, shank, reach and holder; arithmetic access alone is not simulation.

The native path was approximately 359.705 mm, with approximately 467 mm³ removed. Native gouge and holder-collision results were zero. Output-IPW tests confirmed 36 groove points empty and 36 upper/lower/exterior witness points retained, and repeated the earlier main-bore checks. These samples support the repair but do not establish complete dimensional tolerance or real-machine readiness. Record any absent holder/fixture models when interpreting zero collision counts.

A driving solid used to isolate a main bore from an undercut must be clearly identified and hidden, must not replace the design body, and must not be used alone to claim no overcut against the actual design. Verify material to retain as well as material to remove.

## Display and evidence hygiene

Record initial state before inspecting IPW. A facet can be unblanked yet invisible on a hidden layer; count visibility with both blank state and layer state. Hide validated process displays on an appropriate unused layer when that is the intended opening state. Verify after reopen; hiding the display does not repair the stock chain.

`GetInputIpw()` returns a diagnostic faceted body whose lifetime the caller must manage. Repeated reads can accumulate bodies. Only remove bodies proven to be diagnostic; never remove referenced stock to reduce the file size. Temporary observers must be removed from the saved program tree.

Use evidence proportional to the change. For a reference-only repair, compare tools/paths and read the native chain after reopen; do not rerun every machining experiment without a reason. For material-removal changes, inspect actual output IPW and retained geometry. For changed paths, re-post the affected setups and check cutting motion, units, tool numbers and length registers. Keep post warnings, distinguish acceptable approximations from failures, and do not hand-edit NC while claiming fresh NX postprocessing.
