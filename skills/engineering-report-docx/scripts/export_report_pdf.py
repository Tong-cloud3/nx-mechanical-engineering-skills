#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe DOCX -> PDF exporter with Word COM (repaginate + optional TOC update) and LibreOffice fallback."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

WD_ACTIVE_END_ADJ_PAGE = 1
WD_ACTIVE_END_PAGE = 3
WD_STATISTIC_PAGES = 2
WD_EXPORT_PDF = 17


def _find_soffice() -> Path | None:
    for c in (
        os.environ.get("LIBREOFFICE_SOFFICE", ""),
        r"C:\Program Files\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
    ):
        if c and Path(c).is_file():
            return Path(c)
    return None


def export_with_libreoffice(docx_path: Path, out_dir: Path) -> Path:
    soffice = _find_soffice()
    if soffice is None:
        raise FileNotFoundError("LibreOffice soffice.com not found.")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as prof:
        prof_uri = Path(prof).resolve().as_uri()
        cmd = [
            str(soffice),
            f"-env:UserInstallation={prof_uri}",
            "--headless",
            "--nologo",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir.resolve()),
            str(docx_path.resolve()),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode != 0:
            raise RuntimeError(f"LibreOffice failed (rc={res.returncode}): {res.stderr.strip()}")
    pdf_path = out_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Expected PDF not produced: {pdf_path}")
    return pdf_path


def export_with_word(docx_paths: list[Path], out_dir: Path, update_toc: bool, save_docx: bool):
    import win32com.client

    out_dir.mkdir(parents=True, exist_ok=True)
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    results = []
    try:
        for docx_path in docx_paths:
            doc = None
            try:
                doc = word.Documents.Open(str(docx_path.resolve()), ReadOnly=not save_docx)
                if update_toc:
                    for toc in doc.TablesOfContents:
                        toc.Update()
                doc.Repaginate()
                total_pages = int(doc.ComputeStatistics(WD_STATISTIC_PAGES))
                headings = []
                for p in doc.Paragraphs:
                    txt = p.Range.Text.strip()
                    if not txt:
                        continue
                    sname = p.Style.NameLocal if p.Style else ""
                    if sname in ("标题 1", "标题 2", "Heading 1", "Heading 2"):
                        headings.append(
                            {
                                "abs_page": int(p.Range.Information(WD_ACTIVE_END_PAGE)),
                                "adj_page": int(p.Range.Information(WD_ACTIVE_END_ADJ_PAGE)),
                                "title": txt,
                            }
                        )
                if save_docx:
                    doc.Save()
                pdf_path = out_dir / f"{docx_path.stem}.pdf"
                doc.ExportAsFixedFormat(str(pdf_path.resolve()), WD_EXPORT_PDF)
                results.append(
                    {
                        "docx": str(docx_path),
                        "pdf": str(pdf_path),
                        "engine": "word",
                        "total_pages": total_pages,
                        "headings": headings,
                    }
                )
            finally:
                if doc is not None:
                    doc.Close(False)
    finally:
        word.Quit()
    return results


def main():
    import json

    parser = argparse.ArgumentParser(description="Safe DOCX to PDF exporter for engineering reports.")
    parser.add_argument("inputs", nargs="+", type=Path, help="One or more .docx files")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for PDFs")
    parser.add_argument("--engine", choices=("auto", "word", "libreoffice"), default="auto")
    parser.add_argument("--update-toc", action="store_true", help="Refresh TOC fields in Word before export")
    parser.add_argument("--save-docx", action="store_true", help="Save refreshed fields/pagination back to DOCX")
    args = parser.parse_args()

    out = []
    if args.engine in ("auto", "word"):
        try:
            out = export_with_word(args.inputs, args.out_dir, args.update_toc, args.save_docx)
        except Exception as e:
            if args.engine == "word":
                raise
            for p in args.inputs:
                pdf = export_with_libreoffice(p, args.out_dir)
                out.append({"docx": str(p), "pdf": str(pdf), "engine": "libreoffice_fallback", "word_error": repr(e)})
    else:
        for p in args.inputs:
            pdf = export_with_libreoffice(p, args.out_dir)
            out.append({"docx": str(p), "pdf": str(pdf), "engine": "libreoffice"})

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
