# -*- coding: utf-8 -*-
"""REPORT.md -> REPORT.pdf via HTML + headless Edge/Chrome (correct Gujarati shaping).
Usage: python make_pdf.py [REPORT.md] [REPORT.pdf]"""
import pathlib, subprocess, sys
import markdown

ROOT = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "REPORT.md"
dst = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "REPORT.pdf"

CSS = """
@page { size: A4; margin: 14mm 14mm 14mm 14mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Nirmala UI", "Noto Sans Gujarati", "Shruti", "Segoe UI", sans-serif;
       font-size: 9.6pt; line-height: 1.42; color: #1d1d1b; margin: 0; }
h1 { font-size: 16pt; margin: 0 0 4pt; color: #12463a; line-height: 1.25; }
h2 { font-size: 11.5pt; margin: 12pt 0 4pt; color: #12463a; border-bottom: 1px solid #d9d6cf; padding-bottom: 2pt; }
p { margin: 3pt 0 6pt; }
em { color: #55544f; }
a { color: #1f6f5c; text-decoration: none; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 8.6pt; background: #f1efea;
       padding: 0 2pt; border-radius: 2pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 8.8pt; page-break-inside: avoid; }
th, td { border: 1px solid #d9d6cf; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #eef4f1; color: #12463a; font-weight: 600; }
tr:nth-child(even) td { background: #fafaf8; }
ul { margin: 2pt 0 6pt 14pt; padding: 0; }
li { margin: 1pt 0; }
strong { color: #111; }
"""

md = src.read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["tables", "sane_lists"])
html_path = ROOT / "out" / "REPORT.print.html"
html_path.parent.mkdir(exist_ok=True)
title = md.splitlines()[0].lstrip("# ").strip()
html_path.write_text(f"<!doctype html><html lang='gu'><head><meta charset='utf-8'><title>{title}</title>"
                     f"<style>{CSS}</style></head><body>{body}</body></html>", encoding="utf-8")

browsers = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
exe = next(b for b in browsers if pathlib.Path(b).exists())
subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run",
                f"--print-to-pdf={dst}", html_path.resolve().as_uri()], check=True, timeout=120,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"wrote {dst} ({dst.stat().st_size // 1024} KB)")
