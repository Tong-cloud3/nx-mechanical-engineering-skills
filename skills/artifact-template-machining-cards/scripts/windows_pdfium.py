#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render a local PDF to PNG pages through LibreOffice PDFium on Windows."""
import argparse
import ctypes as C
import os
from pathlib import Path
from PIL import Image


def _find_lo_program() -> Path:
    candidates = [
        os.environ.get("LIBREOFFICE_PROGRAM", ""),
        r"C:\Program Files\LibreOffice\program",
        r"C:\Program Files (x86)\LibreOffice\program",
    ]
    for c in candidates:
        if c:
            p = Path(c)
            if (p / "pdfiumlo.dll").is_file():
                return p
    raise FileNotFoundError(
        "pdfiumlo.dll not found. Install LibreOffice or set LIBREOFFICE_PROGRAM."
    )


def pdfpng(path: Path, out: Path, width: int = 2400):
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    lo_dir = _find_lo_program()
    os.add_dll_directory(str(lo_dir))
    f = C.CDLL(str(lo_dir / "pdfiumlo.dll"))

    def sig(name, res, args):
        fn = getattr(f, name)
        fn.restype = res
        fn.argtypes = args
        return fn

    P, I = C.c_void_p, C.c_int
    init_lib = sig("FPDF_InitLibrary", None, [])
    destroy_lib = sig("FPDF_DestroyLibrary", None, [])
    load = sig("FPDF_LoadMemDocument", P, [P, I, C.c_char_p])
    cnt = sig("FPDF_GetPageCount", I, [P])
    load_page = sig("FPDF_LoadPage", P, [P, I])
    wfn = sig("FPDF_GetPageWidth", C.c_double, [P])
    hfn = sig("FPDF_GetPageHeight", C.c_double, [P])
    bmp = sig("FPDFBitmap_Create", P, [I, I, I])
    fill = sig("FPDFBitmap_FillRect", None, [P, I, I, I, I, C.c_uint])
    render = sig("FPDF_RenderPageBitmap", None, [P, P, I, I, I, I, I, I])
    buf = sig("FPDFBitmap_GetBuffer", P, [P])
    stride = sig("FPDFBitmap_GetStride", I, [P])
    closep = sig("FPDF_ClosePage", None, [P])
    closed = sig("FPDF_CloseDocument", None, [P])
    destroy = sig("FPDFBitmap_Destroy", None, [P])

    init_lib()
    doc = None
    paths = []
    try:
        data = path.read_bytes()
        memory = C.create_string_buffer(data)
        doc = load(memory, len(data), None)
        if not doc:
            raise RuntimeError(f"FPDF_LoadMemDocument failed (corrupt or encrypted PDF): {path}")
        out.mkdir(exist_ok=True, parents=True)
        for i in range(cnt(doc)):
            p = load_page(doc, i)
            if not p:
                raise RuntimeError(f"FPDF_LoadPage failed on page {i + 1}: {path}")
            b = None
            try:
                pw, ph = wfn(p), hfn(p)
                h = max(1, round(width * ph / pw))
                b = bmp(width, h, 0)
                if not b:
                    raise RuntimeError(f"FPDFBitmap_Create failed on page {i + 1}")
                fill(b, 0, 0, width, h, 0xFFFFFFFF)
                render(b, p, 0, 0, width, h, 0, 3)
                raw = C.string_at(buf(b), stride(b) * h)
                im = Image.frombytes("RGB", (width, h), raw, "raw", "BGRX", stride(b))
                dst = out / f"{path.stem}_p{i + 1:02}.png"
                im.save(dst, dpi=(145, 145))
                paths.append(dst)
            finally:
                if b:
                    destroy(b)
                closep(p)
    finally:
        if doc:
            closed(doc)
        destroy_lib()
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render a local PDF through LibreOffice PDFium on Windows."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=2400)
    args = parser.parse_args()
    for out_path in pdfpng(args.pdf, args.output, args.width):
        print(out_path)
