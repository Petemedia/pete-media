#!/usr/bin/env python3
"""Browser test (needs playwright). Checks overflow at 3 widths, menu, filters and the booking message."""
import functools, http.server, sys, threading
from pathlib import Path
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent.parent / "dist"
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(*a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_port}/"
bad, errors = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (360, 768, 1440):
        pg = b.new_page(viewport={"width": w, "height": 800}); pg.on("pageerror", lambda e: errors.append(str(e)))
        for f in D.rglob("index.html"):
            path = f.parent.relative_to(D).as_posix()
            pg.goto(base + ("" if path == "." else path + "/"))
            if pg.evaluate("document.documentElement.scrollWidth > innerWidth"): bad.append(f"overflow {path} at {w}")
        pg.goto(base); pg.wait_for_timeout(900); pg.screenshot(path=f"/tmp/home-{w}.png")
        pg.close()
    pg = b.new_page(viewport={"width": 360, "height": 800})
    pg.goto(base); pg.click(".menu")
    if not pg.is_visible("#nav"): bad.append("mobile menu does not open")
    pg.goto(base + "portfolio/"); pg.click("[data-filter=Portraits]")
    if pg.locator(".card:visible").count() != 1: bad.append("filter failed")
    pg.goto(base + "book/"); pg.click("button[type=submit]")
    if pg.locator("#sent a").count(): bad.append("empty form accepted")
    pg.fill("[name=name]", "Test & Person"); pg.fill("[name=phone]", "08000000000"); pg.fill("[name=date]", "2030-01-10"); pg.fill("[name=location]", "Eket")
    pg.select_option("[name=category]", "Wedding"); pg.select_option("[name=coverage]", "Photography"); pg.check("input[type=checkbox]")
    pg.click("button[type=submit]")
    url = unquote(pg.get_attribute("#sent a", "href"))
    for s in ("wa.me/2348138859513", "not yet confirmed", "Test & Person", "Event date: 2030-01-10"):
        if s not in url: bad.append("booking message missing " + s)
    pg.screenshot(path="/tmp/book.png")
    b.close()
srv.shutdown()
print("\n".join(bad + errors) or "PASS: layout at 360/768/1440, menu, filter, booking message")
sys.exit(bool(bad or errors))
