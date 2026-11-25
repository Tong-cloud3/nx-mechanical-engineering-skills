---
name: nx-cam-recovery
description: 在 Siemens NX 中修复和验证 CAM 刀轨、工序间 IPW 传递、毛坯显示、保存重开状态及缺失刀具/组件加载警告，采用隔离候选件与哈希核验后替换正式件。Repair and validate NX CAM toolpaths, IPW handoff, stock display, saved state, and missing tool-component references using isolated candidates and verified promotion.
---

# NX CAM Recovery

Use for an existing CAM part with missing/incorrect paths, stale or broken IPW, unwanted stock display, component load warnings, or save/reopen failures. Use the installed NX API and local documentation; API names and behavior can differ by version.

## Recovery workflow

1. Identify the current master, authorized change, source CAD, operation order, and latest evidence. Check the project lock and live CAD sessions before opening or editing. Keep the user's source geometry and drawings unchanged; test on a copy.
2. Capture initial load status and display **before** CAM initialization or IPW inspection. Preserve every unloaded-part name and status description from `PartLoadStatus` before disposing it.
3. Form a specific hypothesis, make the smallest relevant change, and check the affected behavior. Use the modes below. Stop repeating parameter trials that produce the same failure; inspect the geometry, API contract, or raw error before choosing another approach. Continue other authorized work when a specific dependency is blocked.
4. Save and reopen independently. Check component loading, operation/path status, initial display, and requested IPW behavior. Neither a nonzero cached path nor a successful API/launcher return proves material removal or persistence.
5. Promote only a candidate that passes the requested checks: back up the current master, confirm it has not changed since the candidate was made, stage and hash-check the replacement, then reopen the actual formal path. Synchronize affected NC, delivery copies, entrypoints and manifests; do not overwrite unrelated changes.
6. Report the repaired scope, actual checks, and remaining limitations. A completed diagnostic round is not a completed repair. Distinguish cached paths, native computation, material-removal simulation, postprocessing, and real machine validation.

## 流程图

```mermaid
flowchart TD
    A["确认当前主工程、修复范围与已有证据"] --> B{"具备独占 CAD 操作条件？"}
    B -- 否 --> C["先做独立离线工作，保留现场"]
    C --> B
    B -- 是 --> D["取得项目锁，在副本中工作"]
    D --> E["先记录加载警告与初始显示，再检查 CAM / IPW"]
    E --> F{"定位故障类型"}
    F -- "程序组 / IPW" --> G["核对顺序、工件、毛坯和 MCS；验证动态承接"]
    F -- "缺失组件" --> H["区分装配引用与 CAM 刀具；修复必需引用或清除失效发生件"]
    F -- "缺刀路 / 残料" --> I["核对几何、坐标和刀具可达性；选择合适工序"]
    F -- "显示 / 持久化" --> J["核对隐藏层、分面来源和临时观察工序"]
    G --> K["针对假设作最小修复，按范围验证刀路、IPW、去除与 NC"]
    H --> K
    I --> K
    J --> K
    K --> L["保存、关闭、独立重开候选工程"]
    L --> M{"请求范围内的检查均通过？"}
    M -- 否 --> N["读取原始错误并修正假设；避免重复无效调参"]
    N --> F
    M -- 是 --> O{"正式主工程与记录的源哈希一致？"}
    O -- 否 --> P["保留用户新改动，重新建立候选或合并变更"]
    P --> E
    O -- 是 --> Q["备份、暂存并核对哈希；替换正式文件并同步相关交付"]
    Q --> R["从每个正式交付位置重新打开，核对加载、刀路状态及所需 IPW"]
    R --> S{"正式复核通过？"}
    S -- 否 --> T["停止交付，保留恢复点，定位正式路径中的失败"]
    T --> F
    S -- 是 --> U["报告已修复范围、验证证据与真实限制；释放自有锁"]
```

各分支按本次请求选用；验证项目随改动范围确定。若缺少必要输入或外部条件，记录具体阻碍并继续可独立完成的已授权工作，不把阶段排查当作修复完成。

## Choose the relevant mode

- **Program groups / automatic IPW:** A program folder controls order; workpiece, blank and MCS associations control stock handoff. Trace both trees. Verify native updating with a reversible upstream-order change in a separate copy, restore the order, and verify again after reopen. A frozen stage solid/facet is a snapshot, even when embedded in the same PRT; do not describe it as a dynamic link.
- **Missing component warnings:** Inspect both assembly occurrences and CAM tool definitions. Remove a stale visualization occurrence only after establishing its role; preserve/rebuild required geometry and references. Compare active tool parameters and paths before/after, and require no unresolved load warnings in each formal delivery location. Do not hide the warning by weakening load options. See the component section in the reference.
- **Wrong or incomplete cuts:** Inspect motion endpoints including arcs, source geometry, stock coordinates and accessibility. Validate actual output IPW against both the material to remove and the material to retain. If another machining method is needed, respect the user's chosen scope; distinguish ordinary milling from undercut-capable tooling.
- **Wrong initial display:** Account for blank state **and layer visibility**. `GetInputIpw()` can create/reveal diagnostic facets. Record their provenance and avoid persisting temporary observer operations. Do not delete a facet body that supplies a real blank.

## References

- Read [NX12 repair patterns](references/nx12-repair-patterns.md) for coordinate persistence, specialized tool builders, T-slot access, load-status collection, and evidence examples.
