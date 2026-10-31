#!/usr/bin/env python3
"""Builds downloads/cv-academic.pdf by printing cv.html with headless Google Chrome
and rewrites the PDF metadata (title, author, subject) without tool fingerprints.

Usage (from the site root):  python3 tools/make_pdf.py [extra-output.pdf]
Requires Google Chrome and pypdf (pip install pypdf).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
]
CHROME = next((c for c in CANDIDATES if c and Path(c).exists()), None)
if not CHROME:
    sys.exit("Google Chrome or Chromium not found.")

META = {
    "/Title": "Curriculum Vitae — Everardo Inzunza-González",
    "/Author": "Everardo Inzunza-González",
    "/Subject": "Academic CV. Faculty of Engineering, Architecture and Design, Universidad Autónoma de Baja California",
    "/Keywords": "Everardo Inzunza-González; UABC; FIAD; electronics engineering; curriculum vitae",
}

tmp = tempfile.mkdtemp(prefix="cv-pdf-")   # the OS cleans /tmp; the script deletes nothing
if True:
    raw = Path(tmp) / "raw.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                    f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
                    "--virtual-time-budget=3000", f"--print-to-pdf={raw}",
                    (ROOT / "cv.html").as_uri()], check=True, capture_output=True)
    writer = PdfWriter(clone_from=PdfReader(str(raw)))
    info = DictionaryObject()
    for k, v in META.items():
        info[NameObject(k)] = TextStringObject(v)
    writer._info = writer._add_object(info)          # replaces the browser Creator/Producer
    if "/Metadata" in writer._root_object:
        del writer._root_object["/Metadata"]
    outputs = [ROOT / "downloads" / "cv-academic.pdf"] + [Path(a) for a in sys.argv[1:]]
    for out in outputs:
        with open(out, "wb") as fh:
            writer.write(fh)
        print("Written:", out)
