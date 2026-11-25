#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only DOCX structural and consistency checker for engineering reports."""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

RE_FIG = re.compile(r"图\s*(\d+)\s*[-—.]\s*(\d+)")
RE_TBL = re.compile(r"表\s*(\d+)\s*[-—.]\s*(\d+)")
RE_PLACEHOLDER = re.compile(r"(TODO|TBD|FIXME|待补充|待完善|待填写|XXX|示例课题)", re.IGNORECASE)


def _check_sequence(items):
    """Detect duplicates and numbering gaps within each chapter."""
    by_ch = defaultdict(list)
    seen = Counter()
    for ch, num in items:
        key = f"{ch}-{num}"
        seen[key] += 1
        by_ch[int(ch)].append(int(num))
    dups = sorted(k for k, v in seen.items() if v > 1)
    gaps = []
    for ch, nums in sorted(by_ch.items()):
        uniq = sorted(set(nums))
        expected = list(range(1, max(uniq) + 1))
        missing = [n for n in expected if n not in uniq]
        if missing:
            gaps.append({"chapter": ch, "missing": missing})
    return {"count": len(items), "duplicates": dups, "gaps": gaps}


def check_docx(path: Path) -> dict:
    res = {"file": str(path)}
    with ZipFile(path) as z:
        res["zip_error"] = z.testzip()
        root = ET.fromstring(z.read("word/document.xml"))

    res["page_sizes_mm"] = [
        {
            "width": round(int(x.get(f"{{{W}}}w")) * 25.4 / 1440, 2),
            "height": round(int(x.get(f"{{{W}}}h")) * 25.4 / 1440, 2),
        }
        for x in root.iter(f"{{{W}}}pgSz")
        if x.get(f"{{{W}}}w") and x.get(f"{{{W}}}h")
    ]
    res["tables"] = len(root.findall(f"{{{W}}}body/{{{W}}}tbl"))
    res["inline_figures"] = len(list(root.iter(f"{{{WP}}}inline")))
    res["anchor_figures"] = len(list(root.iter(f"{{{WP}}}anchor")))
    res["omath_equations"] = len(list(root.iter(f"{{{M}}}oMath")))

    fig_caps = []
    tbl_caps = []
    placeholders = []
    paras = list(root.iter(f"{{{W}}}p"))
    res["paragraphs"] = len(paras)

    for idx, p in enumerate(paras):
        txt = "".join(t.text or "" for t in p.iter(f"{{{W}}}t")).strip()
        if not txt:
            continue
        if len(txt) <= 80:
            mf = RE_FIG.match(txt)
            if mf:
                fig_caps.append((mf.group(1), mf.group(2)))
            mt = RE_TBL.match(txt)
            if mt:
                tbl_caps.append((mt.group(1), mt.group(2)))
        mp = RE_PLACEHOLDER.search(txt)
        if mp and len(placeholders) < 20:
            placeholders.append({"para_index": idx, "match": mp.group(0), "snippet": txt[:60]})

    fonts_ea = Counter()
    fonts_ascii = Counter()
    for rf in root.iter(f"{{{W}}}rFonts"):
        ea = rf.get(f"{{{W}}}eastAsia")
        ac = rf.get(f"{{{W}}}ascii")
        if ea:
            fonts_ea[ea] += 1
        if ac:
            fonts_ascii[ac] += 1

    res["figure_captions"] = _check_sequence(fig_caps)
    res["table_captions"] = _check_sequence(tbl_caps)
    res["placeholders"] = placeholders
    res["top_eastAsia_fonts"] = fonts_ea.most_common(6)
    res["top_ascii_fonts"] = fonts_ascii.most_common(6)
    return res


def main():
    parser = argparse.ArgumentParser(description="Read-only DOCX checker for engineering reports.")
    parser.add_argument("path", type=Path, help="Single .docx file or directory containing .docx files")
    args = parser.parse_args()
    files = (
        [args.path]
        if args.path.is_file()
        else sorted(
            x
            for x in args.path.rglob("*.docx")
            if x.is_file() and not x.name.startswith("~$")
        )
    )
    print(json.dumps([check_docx(f) for f in files], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
