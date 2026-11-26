#!/usr/bin/env python3
"""Checks the built site: internal links, titles, one h1, image alts, secrets."""
import re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
D = Path(__file__).resolve().parent.parent / "dist"
bad = []
class P(HTMLParser):
    def __init__(s): super().__init__(); s.links=[]; s.h1=0; s.noalt=0
    def handle_starttag(s, t, a):
        a = dict(a)
        s.h1 += t == "h1"
        if t == "img" and "alt" not in a: s.noalt += 1
        for k in ("href", "src", "poster"):
            if a.get(k): s.links.append(a[k])
files = list(D.rglob("*.html"))
for f in files:
    p = P(); text = f.read_text(); p.feed(text); n = f.relative_to(D)
    if p.h1 != 1: bad.append(f"{n}: {p.h1} h1 elements")
    if p.noalt: bad.append(f"{n}: image without alt")
    if "<title>" not in text: bad.append(f"{n}: no title")
    for l in p.links:
        if re.match(r"^(https?:|tel:|mailto:|#)", l): continue
        t = (f.parent / unquote(l.split("#")[0].split("?")[0])).resolve()
        if t.is_dir(): t = t / "index.html"
        if not t.is_file(): bad.append(f"{n}: broken link {l}")
for f in D.rglob("*"):
    if f.suffix in (".html", ".js", ".json", ".css") and re.search(r"service_role|sk-[A-Za-z0-9]{20}|AIza[0-9A-Za-z_-]{30}", f.read_text()):
        bad.append(f"possible secret in {f.name}")
print("\n".join(bad) or f"PASS: {len(files)} pages, links, headings, alts and secret scan")
sys.exit(bool(bad))
