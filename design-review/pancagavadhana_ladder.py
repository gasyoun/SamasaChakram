#!/usr/bin/env python3
"""H8503 design proof — pañca-gava-dhanaḥ single-staircase ladder.

Q3-confirmed drawing (docs/klammerdiagramm-design-review.md, 20-11-2026).
One hyphenated written line; one open arrow per word at its stem apex;
two left stems joined by one shallow hatched band (rung A); an elbow
connector carries that joined unit down to the lower hatched rung B where
the long right stem of dhanaḥ joins; head marked first-read by a small
caption, not a second arrow; separate "Whose?" semantic step below with no
stem or hatch. Reads klammerdiagramm/klammerdiagramm-pancagavadhana.json;
writes only beside itself (design-review/). Offline PNG via headless local
Chrome. Not published; tracked sources untouched.

Usage: python3 design-review/pancagavadhana_ladder.py
"""

import base64
import json
import os
from pathlib import Path
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC_JSON = os.path.join(ROOT, "klammerdiagramm", "klammerdiagramm-pancagavadhana.json")
SUBSET_WOFF2 = os.path.join(ROOT, "klammerdiagramm", "charis-klammer-subset.woff2")
OUT_SVG = os.path.join(HERE, "pancagavadhana-ladder.svg")
OUT_PNG = os.path.join(HERE, "pancagavadhana-ladder.png")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def text_widths(tokens):
    """Advance widths (px at 1em) for each token string, from the embedded
    Klammer Serif subset (Charis 7.000 Regular metrics, OFL)."""
    from fontTools.ttLib import TTFont

    font = TTFont(SUBSET_WOFF2)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    widths = []
    for tok in tokens:
        total = 0
        for ch in tok:
            gname = cmap.get(ord(ch))
            if gname is None:
                raise SystemExit(f"glyph missing from subset: {ch!r} (token {tok!r})")
            total += hmtx[gname][0]
        widths.append(total / upem)
    return widths


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main():
    with open(SRC_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    assert [node[:3] for node in data["nodes"]] == [
        ["A", 0, 1], ["B", "A", 2]
    ], "this proof requires the confirmed inner pair, then attachment to dhanaḥ"
    tokens = data["tokens"]  # ["pañca", "gava", "dhanaḥ"]
    ii_start = data["II_START"]  # 2 — divider before dhanaḥ
    fs = data["style"]["FS"]  # 46

    # Written line: one hyphenated string; trailing hyphen suppressed.
    written = "-".join(tokens) if not data["trailing_hyphen"] else "-".join(tokens) + "-"
    # Per-token written forms as laid out on the line: hyphens bind to the
    # LEFT token except the final one (no trailing hyphen).
    forms = [t + "-" for t in tokens[:-1]] + [tokens[-1]]
    assert "".join(forms) == written, "token forms must reconstruct the line"

    wem = text_widths(forms)  # em-relative widths
    x0 = 64.0
    xs = [x0]
    for w in wem[:-1]:
        xs.append(xs[-1] + w * fs)
    hyph_w = text_widths(["-"])[0] * fs

    baseline = 150.0
    stems_x = [xs[i] + wem[i] * fs / 2 for i in range(3)]  # word centers

    # Rung geometry (staircase, top-left down to lower-right).
    arrow_apex = baseline + 16.0        # apex of each open arrow, under the word
    arrow_arm_y = arrow_apex + 13.0     # open V arms end here; stem meets the apex
    band_top = 214.0
    band_h = 34.0
    rung_top = 326.0
    rung_h = 27.0

    band_x0 = stems_x[0] - 16.0
    band_x1 = stems_x[1] + 16.0
    elbow_x = band_x1 + 26.0
    head_stem_x = stems_x[2]

    # Head-first marker: caption only, no second arrow.
    marker = "head · read first"

    # Semantic step, visually separated, no stem/hatch.
    sem_rule_y = 386.0
    sem_y1 = 418.0
    sem_y2 = 450.0

    # Divider: dashed rule with a cusp at the hyphen before token ii_start.
    div_y = 64.0
    cusp_x = xs[ii_start] - hyph_w / 2.0  # hyphen belongs to token ii_start-1
    W = max(
        xs[-1] + wem[-1] * fs + 56.0,
        head_stem_x + 130.0,  # room for the head marker
        band_x1 + 240.0,
    )
    W = int(round(W / 10.0) * 10)
    H = 480

    with open(SUBSET_WOFF2, "rb") as fh:
        font_b64 = base64.b64encode(fh.read()).decode("ascii")

    ink = "#14181c"
    p = []
    a = p.append
    a(f'<svg id="pancagavadhana-ladder" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      f'xmlns="http://www.w3.org/2000/svg" role="img" '
      f"font-family=\"'Klammer Serif', Charis, 'Charis SIL', Georgia, serif\">")
    a(f"<title>{esc(data['title'])}</title>")
    a('<desc>Start at dhanaḥ. The inner rung joins pañca to gava. '
      'The second attaches that intact group to dhana. The semantic step '
      'identifies an outside possessor: one whose wealth is five cows.</desc>')
    a(f"""<style>
@font-face {{ font-family:'Klammer Serif';
  src:url(data:font/woff2;base64,{font_b64}) format('woff2'); }}
text {{ fill:{ink}; }}
line, path {{ stroke:{ink}; fill:none; }}
.hatched-band {{ stroke:{ink}; fill:url(#hatch); }}
</style>""")
    a(f'<defs><pattern id="hatch" width="5.5" height="5.5" patternUnits="userSpaceOnUse" '
      f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5.5" '
      f'stroke-width="0.8" stroke="{ink}"/></pattern></defs>')
    a(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff" stroke="none"/>')

    # I/II divider — dashed rule, cusp at the hyphen before dhanaḥ.
    a(f'<g id="divider-ii-rule">')
    a(f'<line x1="40" y1="{div_y}" x2="{cusp_x - 8:.1f}" y2="{div_y}" '
      f'stroke-dasharray="2.5 4.5" stroke-width="1.2"/>')
    a(f'<path d="M{cusp_x - 8:.1f} {div_y:.1f} l8 6 l8 -6" stroke-width="1.2" fill="none"/>')
    a(f'<line x1="{cusp_x + 8:.1f}" y1="{div_y}" x2="{W - 40}" y2="{div_y}" '
      f'stroke-dasharray="2.5 4.5" stroke-width="1.2"/>')
    a(f'<text x="{(40 + cusp_x) / 2:.1f}" y="{div_y - 8:.1f}" font-size="18" '
      f'text-anchor="middle">I</text>')
    a(f'<text x="{(cusp_x + W - 40) / 2:.1f}" y="{div_y - 8:.1f}" font-size="18" '
      f'text-anchor="middle">II</text>')
    a('</g>')

    # Written line — one hyphenated row, one tspan per member.
    a(f'<text id="written-line" y="{baseline:.1f}" font-size="{fs}">')
    for i, form in enumerate(forms):
        tid = "head-dhanah" if i == ii_start else f"token-{tokens[i]}"
        a(f'<tspan id="{tid}" x="{xs[i]:.1f}">{esc(form)}</tspan>')
    a('</text>')

    def open_arrow(x, gid):
        a(f'<path id="{gid}" d="M{x - 6.5:.1f} {arrow_arm_y:.1f} '
          f'L{x:.1f} {arrow_apex:.1f} L{x + 6.5:.1f} {arrow_arm_y:.1f}" '
          f'stroke-width="1.3"/>')

    def stem(x, y2, gid):
        a(f'<line id="{gid}" x1="{x:.1f}" y1="{arrow_apex:.1f}" '
          f'x2="{x:.1f}" y2="{y2:.1f}" stroke-width="1.3"/>')

    def band(x, y, width, height, label_x, label):
        a(f'<rect class="hatched-band" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" '
          f'height="{height:.1f}" stroke-width="1"/>')
        a(f'<rect x="{label_x-15:.1f}" y="{y+1:.1f}" width="30" '
          f'height="{height-2:.1f}" fill="white" stroke="none"/>')
        a(f'<text x="{label_x:.1f}" y="{y+height/2+7:.1f}" '
          f'font-size="22" text-anchor="middle">{label}</text>')

    # Rung A — the two left stems end in ONE joined shallow hatched band.
    a('<g id="rung-a">')
    open_arrow(stems_x[0], "arrow-panca")
    open_arrow(stems_x[1], "arrow-gava")
    stem(stems_x[0], band_top, "stem-panca")
    stem(stems_x[1], band_top, "stem-gava")
    band(band_x0, band_top, band_x1 - band_x0, band_h,
         (stems_x[0] + stems_x[1]) / 2, "A")
    a('</g>')

    # Head — long right stem descends to rung B; marked first-read by caption.
    a('<g id="head">')
    open_arrow(stems_x[2], "arrow-dhanah")
    stem(stems_x[2], rung_top, "head-stem")
    a(f'<text id="head-marker" x="{head_stem_x + 14:.1f}" y="{baseline + 44:.1f}" '
      f'font-size="15" font-style="italic">{esc(marker)}</text>')
    a('</g>')

    # Connector — actual geometric elbow from the joined unit down to rung B.
    a(f'<path id="connector-a-b" d="M{band_x1:.1f} {band_top + band_h / 2:.1f} '
      f'H{elbow_x:.1f} V{rung_top:.1f}" stroke-width="1.3"/>')

    # Rung B — [pañca-gava] -> dhanaḥ: elbow joins the long head stem here.
    a('<g id="rung-b">')
    band(elbow_x, rung_top, head_stem_x + 9 - elbow_x, rung_h,
         (elbow_x + head_stem_x) / 2, "B")
    a('</g>')

    # Semantic step — Whose? -> external referent; no stem, no hatch.
    a('<g id="semantic-step">')
    a(f'<line x1="{band_x0:.1f}" y1="{sem_rule_y:.1f}" x2="{head_stem_x:.1f}" '
      f'y2="{sem_rule_y:.1f}" stroke-dasharray="2.5 4.5" stroke-width="1.0"/>')
    a(f'<text x="{(band_x0 + head_stem_x) / 2:.1f}" y="{sem_y1:.1f}" '
      f'font-size="24" font-style="italic" text-anchor="middle">Whose?</text>')
    a(f'<text x="{(band_x0 + head_stem_x) / 2:.1f}" y="{sem_y2:.1f}" '
      f'font-size="24" text-anchor="middle">one whose wealth is five cows.</text>')
    a('</g>')
    a('</svg>')

    with open(OUT_SVG, "w", encoding="utf-8") as fh:
        fh.write("\n".join(p) + "\n")
    print(f"wrote {OUT_SVG} ({os.path.getsize(OUT_SVG)} bytes, viewBox {W}x{H})")

    # Native-size PNG, offline headless local Chrome.
    if not os.path.exists(CHROME):
        sys.exit(f"Chrome not found at {CHROME}; SVG is the artifact of record")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME, args=["--disable-background-networking"]
        )
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1,
                                color_scheme="light")
        page.route("**/*", lambda route: route.continue_()
                   if route.request.url.startswith(("file:", "data:")) else route.abort())
        page.goto(Path(OUT_SVG).as_uri())
        page.evaluate("document.fonts.ready.then(() => true)")
        page.locator("svg").screenshot(path=OUT_PNG)
        browser.close()
    if not os.path.exists(OUT_PNG):
        sys.exit("Chrome produced no PNG")
    print(f"wrote {OUT_PNG} ({os.path.getsize(OUT_PNG)} bytes, {W}x{H} native)")
    print(f"stems px: pañca={stems_x[0]:.1f} gava={stems_x[1]:.1f} "
          f"dhanaḥ={head_stem_x:.1f}; divider cusp x={cusp_x:.1f}")


if __name__ == "__main__":
    main()
