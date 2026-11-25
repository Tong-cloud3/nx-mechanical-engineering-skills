#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only DOCX/PDF structural inventory; does not validate machining geometry."""
import argparse
import json
import re
from pathlib import Path
from xml.etree import ElementTree as E
from zipfile import ZipFile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
SCHOOL_RE = re.compile(r"[\u4e00-\u9fa5]{2,12}(大学|学院)")


def inspect(path: Path) -> dict:
    result = {"file": str(path)}
    suf = path.suffix.lower()
    if suf == ".docx":
        with ZipFile(path) as z:
            result["zip_error"] = z.testzip()
            root = E.fromstring(z.read("word/document.xml"))
            result["page_sizes_mm"] = [
                {
                    "width": round(int(x.get("{" + W + "}w")) * 25.4 / 1440, 2),
                    "height": round(int(x.get("{" + W + "}h")) * 25.4 / 1440, 2),
                }
                for x in root.iter("{" + W + "}pgSz")
                if x.get("{" + W + "}w") and x.get("{" + W + "}h")
            ]
            result["tables"] = len(root.findall("{" + W + "}body/{" + W + "}tbl"))
            inline_cnt = len(list(root.iter("{" + WP + "}inline")))
            anchor_cnt = len(list(root.iter("{" + WP + "}anchor")))
            result["inline_figures"] = inline_cnt
            result["anchor_figures"] = anchor_cnt
            result["total_figures"] = inline_cnt + anchor_cnt
            all_text = "".join(t.text or "" for t in root.iter("{" + W + "}t"))
            school_hits = sorted(set(m.group(0) for m in SCHOOL_RE.finditer(all_text)))
            if school_hits:
                result["school_name_hits"] = school_hits
    elif suf == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            result["note"] = "pypdf unavailable; inspect PDF with windows_pdfium.py"
        else:
            reader = PdfReader(path)
            result["pages"] = len(reader.pages)
            result["page_sizes_mm"] = [
                {
                    "width": round(float(x.mediabox.width) * 25.4 / 72, 2),
                    "height": round(float(x.mediabox.height) * 25.4 / 72, 2),
                }
                for x in reader.pages
            ]
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Read-only DOCX/PDF structural inventory for machining cards.")
    p.add_argument("path", type=Path)
    a = p.parse_args()
    files = (
        [a.path]
        if a.path.is_file()
        else sorted(x for x in a.path.rglob("*") if x.is_file() and x.suffix.lower() in (".docx", ".pdf"))
    )
    print(json.dumps([inspect(x) for x in files], ensure_ascii=False, indent=2))
