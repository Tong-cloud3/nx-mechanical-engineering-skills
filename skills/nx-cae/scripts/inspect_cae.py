#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only NX Nastran CAE directory inspector (.dat / .f06 / .log / sizes).

Streams large .dat and .f06 files without loading them fully into memory.
Does not modify any engineering files and does not require NX to be running.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

RE_SOL = re.compile(r"^\s*SOL\s+(\S+)", re.IGNORECASE)
RE_UNIT = re.compile(r"(?:UNITSYS\s*=\s*([A-Z0-9_\-]+)|UNITS\s*:\s*([^\r\n]+))", re.IGNORECASE)
RE_EIG_ROW = re.compile(
    r"^\s*(\d+)\s+\d+\s+([+-]?\d+\.\d+E[+-]\d+)\s+([+-]?\d+\.\d+E[+-]\d+)\s+([+-]?\d+\.\d+E[+-]\d+)"
)


def inspect_dat(path: Path) -> dict:
    info = {
        "file": path.name,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "sol": None,
        "unitsys": None,
        "case_control": [],
        "has_print_output": False,
        "has_stress_output": False,
        "has_spcforces_output": False,
        "has_meffmass": False,
        "has_eigrl": False,
        "has_spc_ref": False,
        "spc_card_count": 0,
        "mat1_samples": [],
    }
    in_bulk = False
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not in_bulk:
                up = line.upper()
                if "BEGIN BULK" in up:
                    in_bulk = True
                    continue
                if info["sol"] is None:
                    m = RE_SOL.match(line)
                    if m:
                        info["sol"] = m.group(1)
                if info["unitsys"] is None and "UNITS" in up:
                    m = RE_UNIT.search(line)
                    if m:
                        info["unitsys"] = (m.group(1) or m.group(2)).strip()
                stripped = line.strip()
                if not stripped or stripped.startswith("$"):
                    continue
                su = stripped.upper()
                if any(
                    su.startswith(k)
                    for k in (
                        "DISPLACEMENT",
                        "STRESS",
                        "SPCFORCES",
                        "MEFFMASS",
                        "SPC",
                        "METHOD",
                        "LOAD",
                        "SUBCASE",
                    )
                ):
                    if len(info["case_control"]) < 40:
                        info["case_control"].append(stripped)
                    if "PRINT" in su and any(
                        x in su for x in ("DISPLACEMENT", "STRESS", "SPCFORCES", "ELFORCE")
                    ):
                        info["has_print_output"] = True
                    if su.startswith("STRESS"):
                        info["has_stress_output"] = True
                    if su.startswith("SPCFORCES"):
                        info["has_spcforces_output"] = True
                    if su.startswith("MEFFMASS"):
                        info["has_meffmass"] = True
                    if su.startswith("SPC") and not su.startswith("SPCFORCES"):
                        info["has_spc_ref"] = True
            else:
                if line.startswith(("SPC", "SPC1", "SPCADD")):
                    info["spc_card_count"] += 1
                elif line.startswith(("EIGRL", "EIGR")):
                    info["has_eigrl"] = True
                elif line.startswith("MAT1") and len(info["mat1_samples"]) < 5:
                    info["mat1_samples"].append(line.strip())
    return info


def inspect_log(path: Path) -> dict:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    fatals = [ln.strip() for ln in txt.splitlines() if "FATAL" in ln.upper()][:10]
    return {
        "file": path.name,
        "static_completed": "Linear static analysis completed" in txt,
        "modal_completed": "Normal modes analysis completed" in txt,
        "analysis_complete_0": ("Analysis complete  0" in txt or "Analysis complete 0" in txt),
        "fatal_lines": fatals,
    }


def inspect_f06(path: Path) -> dict:
    info = {
        "file": path.name,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "end_of_job": False,
        "fatal_count": 0,
        "warn_7555_count": 0,
        "eigenvalues_hz": [],
        "modal_eff_mass_last_row": None,
    }
    in_eig = False
    in_meff = False
    with path.open("rb") as f:
        for raw in f:
            if b"USER FATAL MESSAGE" in raw:
                info["fatal_count"] += 1
            if b"WARNING MESSAGE 7555" in raw:
                info["warn_7555_count"] += 1
            if b"END OF JOB" in raw:
                info["end_of_job"] = True
            if b"R E A L   E I G E N V A L U E S" in raw:
                in_eig = True
                continue
            if in_eig:
                line = raw.decode("ascii", errors="ignore")
                m = RE_EIG_ROW.match(line)
                if m:
                    info["eigenvalues_hz"].append(
                        {"mode": int(m.group(1)), "cycles_hz": float(m.group(4))}
                    )
                elif info["eigenvalues_hz"] and (
                    line.strip() == "" or "NX NASTRAN" in line or "\x0c" in line
                ):
                    in_eig = False
            if b"MODAL EFFECTIVE MASS FRACTION" in raw or b"M O D A L   E F F E C T I V E   M A S S   F R A C T I O N" in raw:
                in_meff = True
                continue
            if in_meff:
                line = raw.decode("ascii", errors="ignore").strip()
                if line and line[0].isdigit():
                    info["modal_eff_mass_last_row"] = line
                elif info["modal_eff_mass_last_row"] and (
                    "NX NASTRAN" in line or "\x0c" in line
                ):
                    in_meff = False
    return info


def inspect_dir(target: Path) -> dict:
    files = sorted(p for p in target.iterdir() if p.is_file()) if target.is_dir() else [target]
    sizes_by_ext = defaultdict(int)
    for p in files:
        sizes_by_ext[p.suffix.lower() or "(no_ext)"] += p.stat().st_size
    size_summary_mb = {
        k: round(v / (1024 * 1024), 2)
        for k, v in sorted(sizes_by_ext.items(), key=lambda kv: -kv[1])
    }
    return {
        "target": str(target),
        "total_mb": round(sum(sizes_by_ext.values()) / (1024 * 1024), 2),
        "sizes_by_ext_mb": size_summary_mb,
        "dat_files": [inspect_dat(p) for p in files if p.suffix.lower() == ".dat"],
        "log_files": [inspect_log(p) for p in files if p.suffix.lower() == ".log"],
        "f06_files": [inspect_f06(p) for p in files if p.suffix.lower() == ".f06"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read-only NX Nastran CAE inspector (.dat, .f06, .log, sizes)."
    )
    parser.add_argument("path", type=Path, help="CAE engineering directory or single solver file")
    args = parser.parse_args()
    print(json.dumps(inspect_dir(args.path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
