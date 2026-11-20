#!/usr/bin/env python3
"""export_png.py — clean native-size PNG export for Klammerdiagramm HTML renders.

H8485 (20-11-2026). Reads each committed embedded-font HTML (the render with the
base64 "Klammer Serif" subset), loads it in ONE persistent, fully OFFLINE Google
Chrome context (every request that is not file:// or data: is blocked), light
colour scheme, 1× device scale, and screenshots exactly the <svg> element bounds
— no browser chrome, no page padding, native viewBox dimensions.

Driver: the already-installed playwright package is used ONLY as a CDP driver
pointing at the system Chrome executable — no browser is downloaded and no
profile is created beyond a throwaway temp dir.

Usage (repo root):
  python klammerdiagramm/export_png.py <a.html> <a.png> [<b.html> <b.png> ...]

Each html/png pair is exported in the same persistent context. The PNG lands at
the SVG's native viewBox size (parsed from the HTML's <svg viewBox="0 0 W H">).
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
_BOOT = """([w, h]) => {
    const m = document.querySelector('main');
    if (m) { m.style.maxWidth = 'none'; m.style.margin = '0'; m.style.padding = '0'; }
    const svg = document.querySelector('svg');
    svg.style.width = w + 'px'; svg.style.height = h + 'px'; svg.style.display = 'block';
}"""


def svg_size(html_text: str) -> tuple[int, int]:
    m = re.search(r'<svg[^>]*viewBox="0 0 (\d+) (\d+)"', html_text)
    if not m:
        raise SystemExit("no <svg viewBox=\"0 0 W H\"> found in HTML")
    return int(m.group(1)), int(m.group(2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean native-size PNG export for Klammerdiagramm HTML renders")
    ap.add_argument("--browser", default=CHROME if Path(CHROME).is_file() else None,
                    help="installed Chromium executable (macOS Chrome when present)")
    ap.add_argument("pairs", nargs="+", metavar="html png",
                    help="html png [html png ...] — export each HTML's <svg> element to a native-size PNG")
    args = ap.parse_args()
    if len(args.pairs) % 2:
        ap.error("expected an even list: html png [html png ...]")

    jobs = []
    for i in range(0, len(args.pairs), 2):
        html_p = Path(args.pairs[i])
        png_p = Path(args.pairs[i + 1])
        if not html_p.is_file():
            ap.error(f"{html_p} not found")
        w, h = svg_size(html_p.read_text(encoding="utf-8"))
        jobs.append((html_p, png_p, w, h))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright python package not available (no install needed by "
                 "this script — it drives the system Chrome only)")

    max_w = max(w for _, _, w, _ in jobs) + 16
    max_h = max(h for _, _, _, h in jobs) + 16
    with tempfile.TemporaryDirectory(prefix="klammer-png-") as prof:
        with sync_playwright() as p:
            # ONE persistent Chrome context for the whole batch, light scheme, 1×.
            ctx = p.chromium.launch_persistent_context(
                prof, headless=True, executable_path=args.browser,
                args=["--disable-background-networking", "--disk-cache-size=1048576"],
                color_scheme="light", device_scale_factor=1,
                viewport={"width": max_w, "height": max_h},
            )

            def offline(route):
                # block every non-file/data request — the render must be fully offline
                if route.request.url.startswith(("file://", "data:")):
                    route.continue_()
                else:
                    route.abort()

            ctx.route("**/*", offline)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            for html_p, png_p, w, h in jobs:
                page.goto(html_p.resolve().as_uri(), wait_until="load")
                page.evaluate(_BOOT, [w, h])
                page.evaluate("() => document.fonts.ready")     # embedded WOFF2 settle
                page.query_selector("svg").screenshot(path=str(png_p))
                print(f"wrote {png_p} ({w}x{h})")
            ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
