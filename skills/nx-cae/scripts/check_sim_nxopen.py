#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only NXOpen SIM diagnostic journal for NX 12.

Usage (set environment variables before calling run_journal.exe):
  $env:CAE_SIM_PATH = "C:\\path\\to\\part_analysis.sim"
  $env:CAE_LOG_PATH = "C:\\temp\\sim_check.json"
  & "<NX_INSTALL_DIR>\\NXBIN\\run_journal.exe" check_sim_nxopen.py

Does NOT modify or save the SIM file.
"""
import json
import os
import traceback

import NXOpen
import NXOpen.CAE


def main():
    sim_path = os.environ.get("CAE_SIM_PATH", "").strip()
    log_path = os.environ.get("CAE_LOG_PATH", "").strip()
    report = {"sim_path": sim_path, "ok": False, "solutions": [], "error": None}
    try:
        if not sim_path or not os.path.exists(sim_path):
            raise FileNotFoundError(f"CAE_SIM_PATH not found: {sim_path!r}")

        os.chdir(os.path.dirname(os.path.abspath(sim_path)))
        s = NXOpen.Session.GetSession()
        try:
            s.Parts.LoadOptions.UsePartialLoading = False
        except Exception:
            pass

        part, load_status = s.Parts.OpenBaseDisplay(sim_path)
        unloaded = []
        try:
            for i in range(load_status.NumberUnloadedParts):
                unloaded.append(
                    {
                        "part": load_status.GetPartName(i),
                        "status": load_status.GetStatus(i),
                        "desc": load_status.GetStatusDescription(i),
                    }
                )
        finally:
            load_status.Dispose()
        report["unloaded_parts"] = unloaded

        sim = part.Simulation
        report["active_solution"] = sim.ActiveSolution.Name if sim.ActiveSolution else None
        report["all_constraints"] = [
            {"name": c.Name, "descriptor": c.DescriptorName} for c in sim.Constraints
        ]

        or_tags = {}
        for sol in sim.Solutions:
            sinfo = {
                "name": sol.Name,
                "solver": getattr(sol, "SolverType", None),
                "step_count": sol.StepCount,
                "bcs": [{"name": b.Name, "descriptor": b.DescriptorName} for b in sol.GetBcs()],
                "lanczos": None,
                "output_requests": None,
                "result_ref": None,
                "result_readable": None,
            }
            try:
                lan = sol.PropertyTable.GetNamedPropertyTablePropertyValue("Lanczos Method")
                if lan is not None:
                    lpt = lan.PropertyTable
                    sinfo["lanczos"] = {
                        "name": lan.Name,
                        "ND": lpt.GetIntegerPropertyValue("ND"),
                    }
            except Exception:
                pass
            try:
                oreq = sol.PropertyTable.GetNamedPropertyTablePropertyValue("Output Requests")
                if oreq is not None:
                    sinfo["output_requests"] = {"name": oreq.Name, "tag": int(oreq.Tag)}
                    or_tags.setdefault(int(oreq.Tag), []).append(sol.Name)
            except Exception:
                pass
            try:
                rref = sol.GetResultReferenceByIndex(0)
                sinfo["result_ref"] = {
                    "file": rref.GetResultFile(),
                    "units": [u.Name if u else None for u in rref.GetResultFileUnits()],
                }
            except Exception as e:
                sinfo["result_ref"] = {"error": repr(e)}
            try:
                res = s.ResultManager.CreateSolutionResult(sol)
                iters = []
                for lc in res.GetLoadcases():
                    for it in lc.GetIterations()[:12]:
                        iters.append({"name": it.Name, "value": getattr(it, "Value", None)})
                sinfo["result_readable"] = {
                    "ok": True,
                    "nodes": res.AskNumNodes(),
                    "elements": res.AskNumElements(),
                    "loadcases": res.AskNumLoadcases(),
                    "iterations_preview": iters,
                }
            except Exception as e:
                sinfo["result_readable"] = {"ok": False, "error": repr(e)}
            report["solutions"].append(sinfo)

        report["shared_output_requests"] = {
            str(tag): names for tag, names in or_tags.items() if len(names) > 1
        }
        report["ok"] = True
        part.Close(
            NXOpen.BasePart.CloseWholeTree.TrueValue,
            NXOpen.BasePart.CloseModified.CloseModified,
            None,
        )
    except Exception:
        report["error"] = traceback.format_exc()

    out_txt = json.dumps(report, ensure_ascii=False, indent=2)
    if log_path:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(out_txt)
    else:
        print(out_txt)


if __name__ == "__main__":
    main()
