import sys, os, json, math, base64
sys.stdout.reconfigure(encoding="utf-8")
from indic_transliteration import sanscript

def _has_cyr(t):
    return any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in t)

def deva(t):
    # Devanagari twin of an IAST label; non-Sanskrit (RU/mixed) labels stay as-is
    if _has_cyr(t):
        return t
    return sanscript.transliterate(t, sanscript.IAST, sanscript.DEVANAGARI)

# ---------------------------------------------------------------------------
# The samāsa-cakra wheel (H1016, 16-07-2026) — the repo's eponymous deliverable:
# a rotatable radial classification chart of the Sanskrit compound system,
# built from the Leitan-crosswalked taxonomy (samasacakra-taxonomy.json) and
# the MG rulings (direction law, dvandva flat, D1–D6).
#
# Rings: hub "samāsa-cakra" · ring 1 = classes (Patañjali's pradhāna scheme) ·
# ring 2 = families · ring 3 = leaf subtypes, one canonical example each (click
# for vigraha + RU gloss in the HTML). These are the three named rows of the
# type-size scale: classes 20, families 19, leaves 18 px — one size per row,
# never an exception for an individual example (MG ruling 25-11-2026).
# The dvandva class label is omitted from ring 1 (its 2-leaf arc is too narrow);
# dvandva is still named in ring 2, beside "значения по Пан. 2.1.6".
# Angular width ∝ leaf count.
# Colors: the four validated categorical hues (dataviz palette, light+dark
# modes both validated); identity is never color-alone — every segment carries
# a direct ink label and 2px surface gaps separate all fills.
# Emits samasacakra-wheel.svg (static, light) and samasacakra-wheel.html
# (embedded Klammer Serif, dark mode, hover, click panel, drag-to-rotate).
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
WOFF2 = os.path.join(HERE, "..", "klammerdiagramm", "charis-klammer-subset.woff2")
WOFF2_ITA = os.path.join(HERE, "..", "klammerdiagramm", "charis-klammer-italic-subset.woff2")
WOFF2_DEVA = os.path.join(HERE, "noto-deva-klammer-subset.woff2")
FONT = "'Klammer Serif', 'Charis SIL', Charis, Georgia, serif"

def load_diagram(fname):
    # inline a Klammerdiagramm SVG for a leaf's detail panel. The plate SVGs are
    # fully currentColor (strokes + text + hatch), so they inherit the panel's
    # theme ink; the page already embeds Klammer Serif, which they reference.
    with open(os.path.join(HERE, "..", "klammerdiagramm", fname), encoding="utf-8") as fh:
        return fh.read()

CX = CY = 560
R_HUB, R1a, R1b, R2a, R2b, R3a, R3b = 96, 102, 186, 192, 288, 294, 500
GAP_DEG = 0.0          # gaps drawn as surface-color strokes, not angular gaps

GALLERY_URL = "https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm-worked-examples.md"
PAGES = "https://gasyoun.github.io/SamasaChakram/"
T = json.load(open(os.path.join(HERE, "samasacakra-taxonomy.json"), encoding="utf-8"))

# --- H8573 pilot layer -----------------------------------------------------
# Three things the approved five-lesson pilot adds to the wheel (design branch
# design/drumam-wheel, reports/DRUMAM_WHEEL_DESIGN_24-11-2026.md):
#   1. a stable clockwise leaf number, drawn in its own layer so a frequency
#      mode change can never hide it;
#   2. a corpus-share layer with ONE legend (>=5% / 1-<5% / <1% / no comparable
#      share) switchable between traffic-light, hatching and outline — shares
#      only where a corpus tag matches a leaf exactly (ADR 0002);
#   3. kevala-samasa as a separate entry beside the wheel (conspectus § 8) plus
#      legacy-id resolution (ekadesin -> the merged prathama leaf).
# All pilot content lives in pilot_data.json; this file only renders it.
PILOT = json.load(open(os.path.join(HERE, "pilot_data.json"), encoding="utf-8"))
FREQ = PILOT["frequency"]
BANDS = [b["id"] for b in FREQ["bands"]]
# Only a MEASURED, exactly-matched share may use the three visual bands. The
# conspectus' section-14 estimates are card notes: no band, no colour, no rank
# (ADR 0002; reviewer ruling 24-11-2026).
LEAF_FREQ = {e["target"]: e for e in FREQ["entries"]
             if e["scope"] == "leaf" and e["kind"] == "share"}
LEAF_EST = {e["target"]: e for e in FREQ["entries"]
            if e["scope"] == "leaf" and e["kind"] == "estimate"}
GROUP_FREQ = {e["target"]: e for e in FREQ["entries"] if e["scope"] == "group"}
RANKED = sorted(LEAF_FREQ.values(), key=lambda e: -e["pct"])
ALIAS = PILOT["legacy_leaf_aliases"]
LESSON_BY_LEAF = {l["leaf"]: l for l in PILOT["lessons"]}
PARA_LESSONS = {}
for _l in PILOT["lessons"]:
    for _p in _l["paras"]:
        PARA_LESSONS.setdefault(_p, []).append(_l)


BAND_LABEL = {b["id"]: b["label"] for b in PILOT["frequency"]["bands"]}
# One size for every leaf of the outer row (18px). The size ladder is by row
# (classes 20 / families 19 / leaves 18), never by an individual example.
LEAF_SIZE = 18
# Family labels are stacked along the rim; the first line is the outer one.
FAMILY_LABEL_BREAKS = {
    "значения по Пан. 2.1.6": "значения\nпо Пан. 2.1.6",
    "vibhakti-tatpuruṣa": "vibhakti\n-tatpuruṣa",
    "особые татпуруши": "особые\nтатпуруши",
    "samānādhikaraṇa": "samānādhi\n-karaṇa",
    "vyadhikaraṇa": "vya-\ndhi-\nkaraṇa",
    "особые бахуврихи": "особые\nбахуврихи",
    "dvandva": "dvan\n-dva",
}


def freq_line(lid):
    """The card's MEASURED line: an exact table-5 share with its rank, or the
    explicit statement that no comparable share exists."""
    e = LEAF_FREQ.get(lid)
    if e:
        count = f'{e["count"]:,}'.replace(",", " ")
        rank = RANKED.index(e) + 1
        return (f'Корпусная доля: <b>{e["pct"]:.2f}%</b> ({e["tag"]}, '
                f'{count} из ~64 тыс.; таблица 5, Kulkarni &amp; Kumar 2013). '
                f'Корпусный ранг: <b>{rank} из {len(RANKED)}</b> — место по доле среди '
                f'тегов с измеренной долей, не среди всех подтипов (ADR 0002)')
    return ('Корпусная доля: <b>нет сопоставимой доли</b> — в таблице 5 нет тега, '
            'совпадающего с лепестком (ADR 0002)')


def est_line(lid):
    """The conspectus estimate, kept strictly apart from the measured layer."""
    e = LEAF_EST.get(lid)
    return e["note"] if e else ""


def group_est_line(fid):
    e = GROUP_FREQ.get(fid)
    return ('Оценка конспекта § 14 для всей группы avyayībhāva: ' + e["note"].split(': ', 1)[-1]) if e else ""


def band_of(lid):
    e = LEAF_FREQ.get(lid)
    return e["band"] if e else "none"

classes = T["classes"]
total_leaves = sum(len(f["leaves"]) for c in classes for f in c["families"])
UNIT = 360.0 / total_leaves
# Initial tilt (MG ruling 25-11-2026): leaf 1 (prathamā / ekadeśin) rests on the
# left equator. The offset is baked into the geometry — NOT applied as a group
# transform — so the labels are re-oriented at their new positions and the hub
# text stays upright. A double click resets any drag to this baked-in zero.
INIT_ROT = -(90.0 + UNIT / 2)

def eff(a_deg):
    return a_deg + INIT_ROT

def pol(r, a_deg):
    a = math.radians(eff(a_deg) - 90)     # 0° at 12 o'clock, clockwise
    return CX + r * math.cos(a), CY + r * math.sin(a)

def arc_path(r0, r1, a0, a1):
    large = 1 if (a1 - a0) > 180 else 0
    x0o, y0o = pol(r1, a0); x1o, y1o = pol(r1, a1)
    x0i, y0i = pol(r0, a1); x1i, y1i = pol(r0, a0)
    return (f"M{x0o:.2f} {y0o:.2f} A{r1} {r1} 0 {large} 1 {x1o:.2f} {y1o:.2f} "
            f"L{x0i:.2f} {y0i:.2f} A{r0} {r0} 0 {large} 0 {x1i:.2f} {y1i:.2f} Z")

def dual(fn, *args, **kw):
    # emit the IAST label + its hidden Devanagari twin
    text = args[2] if fn is radial_label else args[3]
    out = fn(*args, **kw)
    d = deva(text)
    if fn is radial_label:
        out += fn(args[0], args[1], d, args[3], args[4] + " l-deva")
    else:
        out += fn(args[0], args[1], args[2], d, args[4], args[5] + " l-deva")
    return out

def number_label(r, a, text):
    # the leaf's clockwise number, set tangentially at the rim (clock-face read);
    # the rotation is folded into (-90, 90] so no number is ever upside down
    x, y = pol(r, a)
    rot = ((eff(a) + 90) % 180) - 90
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="11" class="lbl num" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">{text}</text>')

def radial_label(r, a, text, size, cls):
    # text runs along the radius; flipped on the left half so it reads outward.
    # A newline becomes a stacked tspan pair, so long family names such as
    # vyadhi-/karaṇa keep the same font size as every other family label.
    x, y = pol(r, a)
    ea = eff(a)
    rot = ea - 90 if ea % 360 <= 180 else ea + 90
    anchor = "start" if ea % 360 <= 180 else "end"
    lines = text.split("\n")
    body = (lines[0] if len(lines) == 1 else "".join(
        f'<tspan x="{x:.1f}" dy="{0 if i == 0 else size * 1.05:.1f}">{line}</tspan>'
        for i, line in enumerate(lines)))
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" class="{cls}" '
            f'text-anchor="{anchor}" dominant-baseline="middle" '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">{body}</text>')

def tangential_label(r, a0, a1, text, size, cls):
    a = (a0 + a1) / 2
    x, y = pol(r, a)
    ea = eff(a)
    rot = ea if 90 <= ea % 360 <= 270 else ea       # tangential; flip bottom half
    rot = ea + 180 if 90 < ea % 360 < 270 else ea
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" class="{cls}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">{text}</text>')

# Class and family names follow the rim: an invisible arc per label carries a
# <textPath>. The arc is widened to fit the text at the fixed font size, and
# reversed on the lower half so the letters never finish upside down.
LABEL_ARCS = []

def arc_label_path(r, a0, a1, text, size):
    mid = (a0 + a1) / 2
    need = max(len(x) for x in text.split("\n")) * 0.55 * size / r * (180 / math.pi)
    span = max(a1 - a0, need)
    lo, hi = mid - span / 2, mid + span / 2
    # pol() already applies the initial tilt; only the reading-direction test
    # needs the effective angle, never the path endpoints (no double offset).
    if 90 < eff(mid) % 360 < 270:
        x0, y0 = pol(r, hi); x1, y1 = pol(r, lo)
        sweep, large = 0, 1 if (hi - lo) > 180 else 0
    else:
        x0, y0 = pol(r, lo); x1, y1 = pol(r, hi)
        sweep, large = 1, 1 if (hi - lo) > 180 else 0
    return f'M{x0:.2f} {y0:.2f} A{r} {r} 0 {large} {sweep} {x1:.2f} {y1:.2f}'

def arc_label(pid, text, size, cls):
    return (f'<text font-size="{size}" class="{cls}" text-anchor="middle" '
            f'dominant-baseline="middle">'
            f'<textPath href="#{pid}" startOffset="50%">{text}</textPath></text>')

def emit_arc_label(r, a0, a1, text, size, cls, pid):
    lines = text.split("\n")
    dlines = deva(text).split("\n")
    out = []
    # On the lower half of the wheel a larger radius sits visually LOWER, so
    # the first line must be inner; on the upper half it must be outer. Either
    # way the stacked lines read top-to-bottom, never back-to-front.
    first_inner = 90 < eff((a0 + a1) / 2) % 360 < 270
    for i, line in enumerate(lines):
        # a broken label gets one arc per syllable, stacked across the ring
        offset = (i - (len(lines) - 1) / 2) * size * 1.15
        rr = r + offset if (len(lines) > 1 and first_inner) else (r - offset if len(lines) > 1 else r)
        lid = f'{pid}-{i}' if len(lines) > 1 else pid
        LABEL_ARCS.append(f'<path id="{lid}" d="{arc_label_path(rr, a0, a1, line, size)}" '
                          f'fill="none" stroke="none"/>')
        dline = dlines[i] if i < len(dlines) else deva(line)
        out.append(arc_label(lid, line, size, cls))
        out.append(arc_label(lid, dline, size, cls + " l-deva"))
    return "".join(out)

svg, meta = [], {}
svg.append('<g id="wheel">')
leaf_no = 0          # stable clockwise leaf number, 1..58 from 12 o'clock
nums = []            # its own layer: appended last, never repainted by a mode
a = 0.0
for c in classes:
    n_c = sum(len(f["leaves"]) for f in c["families"])
    span_c = n_c * UNIT
    svg.append(f'<path d="{arc_path(R1a, R1b, a, a + span_c)}" class="seg c-{c["id"]} ring1" data-id="{c["id"]}"/>')
    # class names run ALONG the rim on their own arc (textPath)
    # dvandva's two-leaf arc is too narrow for a 20px class label; keep the
    # segment and its card, drop the ring-1 label — the family row still names
    # dvandva beside "значения по Пан. 2.1.6" (MG ruling 25-11-2026).
    if c["id"] != "dvandva":
        svg.append(emit_arc_label((R1a + R1b) / 2, a, a + span_c, c["name"], 20,
                                  "lbl lbl1", f'arc-c-{c["id"]}'))
    meta[c["id"]] = {"kind": "class", "name": c["name"], "pradhana": c["pradhana"],
                     "structure": c["structure"], "class": c["name"], "cid": c["id"],
                     "freq": "", "n": None}
    af = a
    for f in c["families"]:
        span_f = len(f["leaves"]) * UNIT
        fid = f'{c["id"]}--{f["id"]}'
        svg.append(f'<path d="{arc_path(R2a, R2b, af, af + span_f)}" class="seg c-{c["id"]} ring2" data-id="{fid}"/>')
        fname = f["name"]
        # family names follow the same rim arc; narrow sectors get syllable breaks
        fname_label = FAMILY_LABEL_BREAKS.get(fname, fname)
        svg.append(emit_arc_label((R2a + R2b) / 2, af, af + span_f, fname_label, 19,
                                  "lbl lbl2r", f'arc-f-{fid}'))
        meta[fid] = {"kind": "family", "name": fname, "class": c["name"], "cid": c["id"],
                     "pradhana": c["pradhana"], "structure": c["structure"],
                     # a corpus tag that covers several leaves is published at the
                     # GROUP, never repeated at each of its leaves (ADR 0002)
                     "freq": "", "est": group_est_line(fid),
                     "n": None}
        al = af
        for leaf in f["leaves"]:
            lid = f'{c["id"]}--{f["id"]}--{leaf["id"]}'
            n = leaf_no + 1                      # clockwise from 12 o'clock
            leaf_no = n
            band = band_of(lid)
            d = arc_path(R3a, R3b, al, al + UNIT)
            svg.append(f'<path d="{d}" class="seg c-{c["id"]} ring3" data-id="{lid}" '
                       f'data-n="{n}" data-band="{band}"/>')
            # the frequency overlay carries the share and nothing else: the mode
            # classes below turn its fill/patterm/stroke on, so switching modes
            # never touches the class identity fill or the leaf number
            svg.append(f'<path d="{d}" class="fov c-{c["id"]}" data-band="{band}"/>')
            # one size for every leaf of the outer row (18px)
            svg.append(dual(radial_label, R3a + 8, al + UNIT / 2, leaf["term"], LEAF_SIZE, "lbl lbl3"))
            nums.append(number_label(R3b - 12, al + UNIT / 2, str(n)))
            lz = LESSON_BY_LEAF.get(lid)
            meta[lid] = {"kind": "leaf", "name": leaf["term"], "class": c["name"], "cid": c["id"],
                         "family": fname, "pradhana": c["pradhana"], "structure": c["structure"],
                         "ex": leaf["ex"], "vigraha": leaf["vigraha"], "ru": leaf["ru"],
                         "ex_d": deva(leaf["ex"]), "vigraha_d": deva(leaf["vigraha"]),
                         "note": leaf.get("note", ""),
                         "n": n, "band": band, "freq": freq_line(lid),
                         "est": est_line(lid),
                         "paras": [{"num": p, "href": f'{PAGES}paragrafy/#p-{p.replace(".", "-")}'}
                                   for p in (lz["paras"] if lz else [])],
                         "lesson": ({"title": lz["title"], "href": f'{PAGES}uroki/{lz["slug"]}.html'}
                                    if lz else None),
                         "diagram": "".join(f'<div class="dwrap">{load_diagram(dg)}</div>' for dg in ([leaf["diagram"]] if isinstance(leaf.get("diagram"), str) else leaf.get("diagram", [])))}
            al += UNIT
        af += span_f
    a += span_c

svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_HUB}" class="hub"/>')
svg.append(f'<text x="{CX}" y="{CY - 10}" font-size="34" class="lbl hublbl" text-anchor="middle">samāsa</text>')
svg.append(f'<text x="{CX}" y="{CY + 26}" font-size="20" class="lbl hublbl2" text-anchor="middle">cakra</text>')
svg.append(f'<text x="{CX}" y="{CY - 10}" font-size="34" class="lbl hublbl l-deva" text-anchor="middle">समास</text>')
svg.append(f'<text x="{CX}" y="{CY + 26}" font-size="20" class="lbl hublbl2 l-deva" text-anchor="middle">चक्र</text>')
svg.extend(nums)
svg.append('</g>')
assert leaf_no == total_leaves, (leaf_no, total_leaves)

# kevala-samasa has no leaf on the wheel (conspectus § 8: outside the four
# pradhana classes), so it gets a card of its own, reached from the chip beside
# the wheel — the same panel, the same stable-id routing.
K = PILOT["kevala"]
meta["kevala"] = {"kind": "kevala", "name": K["title"], "class": "", "family": "",
                  "ex": K["card"]["ex"], "vigraha": K["card"]["vigraha"],
                  "ru": K["card"]["ru"], "note": K["card"]["note"],
                  "ex_d": deva(K["card"]["ex"]), "vigraha_d": deva(K["card"]["vigraha"]),
                  "pradhana": "", "structure": "", "freq": "", "n": None,
                  "paras": [{"num": K["para"], "href": f'{PAGES}paragrafy/#p-{K["para"]}'}],
                  "lesson": {"title": "Урок 5 · kevala-samāsa",
                             "href": f'{PAGES}uroki/05-kevala-samasa.html'},
                  "context": K["card"]["context"], "rule": K["card"]["rule"],
                  "second_ex": K["card"]["second_ex"], "diagram": ""}

STYLE_LIGHT = """
.seg { stroke: var(--surface); stroke-width: 2; cursor: pointer; }
.ring1 { fill-opacity: .50; } .ring2 { fill-opacity: .30; } .ring3 { fill-opacity: .16; }
.c-tatpurusa { fill: #2a78d6; } .c-bahuvrihi { fill: #1baf7a; }
.c-dvandva { fill: #d99b00; } .c-avyayibhava { fill: #b8a300; }
.hub { fill: var(--surface); stroke: var(--line); stroke-width: 1.4; }
.lbl { fill: var(--ink); pointer-events: none; }
.lbl2r, .lbl3 { fill: var(--ink2); }
.num { fill: var(--ink); font-weight: bold; opacity: .75; }
.fov { display: none; pointer-events: none; }
.hublbl2 { fill: var(--ink2); }
.seg:hover { fill-opacity: .72; }
.l-deva { display: none; }
"""

LABEL_DEFS = "".join(LABEL_ARCS)

svg_doc = (f'<svg viewBox="0 0 {2*CX} {2*CY}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f"font-family=\"{FONT}\">"
           f'<title>samāsa-cakra</title>'
           f'<desc>The wheel of Sanskrit compounds: four classes, their families and leaf subtypes, '
           f'from the Leitan-crosswalked taxonomy with the MG structural rulings.</desc>'
           f'<defs>{LABEL_DEFS}</defs>'
           f'<style>:root {{ --surface:#fcfcfb; --ink:#20201d; --ink2:#5d5c55; --line:#ddd8cc; }}\n{STYLE_LIGHT}</style>'
           f'<rect width="100%" height="100%" fill="#fcfcfb"/>'
           + "".join(svg) + "</svg>")

with open(os.path.join(HERE, "samasacakra-wheel.svg"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(svg_doc)
print("wrote samasacakra-wheel.svg", len(svg_doc) // 1024, "KB")

b64 = base64.b64encode(open(WOFF2, "rb").read()).decode("ascii")
b64i = base64.b64encode(open(WOFF2_ITA, "rb").read()).decode("ascii")
b64d = base64.b64encode(open(WOFF2_DEVA, "rb").read()).decode("ascii")
meta_json = json.dumps(meta, ensure_ascii=False)
# hatch patterns for the corpus-share layer (mode "штриховка"): the fill is
# strokes on transparent, so the class hue underneath stays visible and the
# band is read a second time by texture alone
BAND_STROKE = {"gte20": 3.2, "10to20": 2.8, "5to10": 2.4, "1to5": 2.0, "none": 1.2}
PATTERNS = "".join(
    f'<pattern id="pat-{bid}" width="8" height="8" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
    f'<rect width="8" height="8" fill="none"/>'
    f'<line x1="0" y1="0" x2="0" y2="8" stroke="#4a4842" stroke-width="{BAND_STROKE[bid]}"/></pattern>'
    for bid in BANDS)
# the inline SVG for HTML drops the internal <style>/<rect> (the page styles it)
svg_inline = ('<svg id="cakra" class="mode-none" viewBox="0 0 1120 1120" role="img" '
              f"font-family=\"{FONT}\">"
              f"<defs>{LABEL_DEFS}{PATTERNS}</defs>" + "".join(svg) + "</svg>")

html = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>samāsa-cakra — колесо санскритских композитов</title>
<style>
@font-face { font-family: 'Klammer Serif'; font-style: normal; src: url(data:font/woff2;base64,__B64__) format('woff2'); }
/* a real Italic face: <em>/<i> and font-style:italic must not be a synthesised slant */
@font-face { font-family: 'Klammer Serif'; font-style: italic; src: url(data:font/woff2;base64,__B64I__) format('woff2'); }
@font-face { font-family: 'Klammer Deva'; src: url(data:font/woff2;base64,__B64D__) format('woff2'); }
:root { --surface:#fcfcfb; --ink:#20201d; --ink2:#5d5c55; --line:#ddd8cc; --panel:#ffffff; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme=light]) { --surface:#1a1a19; --ink:#f2efe6; --ink2:#b5b2a5; --line:#3c3a33; --panel:#232320;
    --c-tatpurusa:#3987e5; --c-bahuvrihi:#199e70; --c-dvandva:#e0b33c; --c-avyayibhava:#c8b84a; }
}
:root[data-theme=dark] { --surface:#1a1a19; --ink:#f2efe6; --ink2:#b5b2a5; --line:#3c3a33; --panel:#232320;
  --c-tatpurusa:#3987e5; --c-bahuvrihi:#199e70; --c-dvandva:#e0b33c; --c-avyayibhava:#c8b84a; }
:root { --c-tatpurusa:#2a78d6; --c-bahuvrihi:#1baf7a; --c-dvandva:#d99b00; --c-avyayibhava:#b8a300; }
html,body { margin:0; background:var(--surface); color:var(--ink); font-family:'Klammer Serif',Georgia,serif; }
main { max-width:1500px; margin:0 auto; padding:20px 16px; display:flex; gap:20px; flex-wrap:wrap; }
#wheelbox { flex:1 1 520px; min-width:340px; }
#wheelbox svg { display:block; width:100%; height:auto; touch-action:none;
  max-width:calc(100vh - 40px); margin:0 auto; }
#panel .repolink svg { width:18px; height:18px; flex:none; }
.seg { stroke:var(--surface); stroke-width:2; cursor:pointer; transition:fill-opacity .12s; }
.ring1 { fill-opacity:.50; } .ring2 { fill-opacity:.30; } .ring3 { fill-opacity:.16; }
.c-tatpurusa { fill:var(--c-tatpurusa); } .c-bahuvrihi { fill:var(--c-bahuvrihi); }
.c-dvandva { fill:var(--c-dvandva); } .c-avyayibhava { fill:var(--c-avyayibhava); }
.seg:hover, .seg.sel { fill-opacity:.74; }
.fov { fill:none; }   /* corpus-share layer: inert until a mode class styles it */
.hub { fill:var(--surface); stroke:var(--line); stroke-width:1.4; }
.lbl { fill:var(--ink); pointer-events:none; }
.lbl2r,.lbl3,.hublbl2 { fill:var(--ink2); }
.l-deva { display:none; font-family:'Klammer Deva','Nirmala UI',serif; }
body.deva .l-iast-hide, body.deva svg text.lbl:not(.l-deva) { display:none; }
body.deva svg text.l-deva { display:block; }
#scripttoggle { margin-left:auto; display:inline-flex; gap:0; border:1px solid var(--line); border-radius:5px; overflow:hidden; }
#scripttoggle button { font:inherit; font-size:.85rem; padding:3px 12px; border:0; background:transparent; color:var(--ink2); cursor:pointer; }
#scripttoggle button.on { background:var(--c-tatpurusa); color:#fff; }
.pdeva { font-family:'Klammer Deva','Nirmala UI',serif; color:var(--ink); }
#panel .pdeva { margin-top:.6em; font-size:.92rem; line-height:1.6; }
#panel { flex:0 1 340px; min-width:300px; background:var(--panel); border:1px solid var(--line);
  border-radius:6px; padding:18px 20px; align-self:flex-start; position:sticky; top:16px;
  max-height:calc(100vh - 32px); overflow:auto; overflow-wrap:anywhere; }
.panel-controls { border-top:1px dashed var(--line); margin-top:14px; padding-top:12px; }
.repolink { display:inline-flex; align-items:center; gap:7px; color:var(--ink2); text-decoration:none;
  font-size:.85rem; margin:0 0 12px; }
.repolink:hover { color:var(--ink); }
#panel h2 { margin:0 0 2px; font-size:1.3rem; font-weight:normal; }
#panel .chain { color:var(--ink2); font-size:.85rem; margin-bottom:10px; }
#panel .ex { font-size:1.15rem; margin:.5em 0 .1em; }
#panel .vig { color:var(--ink2); font-style:italic; }
#panel .ru { margin-top:.4em; }
#panel .rule,#panel .note { font-size:.85rem; color:var(--ink2); border-top:1px dashed var(--line);
  margin-top:12px; padding-top:8px; overflow-wrap:anywhere; }
#panel .diagram { margin:12px 0 0; padding-top:10px; border-top:1px dashed var(--line); color:var(--ink); }
#panel .diagram svg { width:100%; height:auto; display:block; }
#panel .dwrap + .dwrap { margin-top:10px; border-top:1px dotted var(--line); padding-top:10px; }
#panel .diagram figcaption { font-size:.78rem; color:var(--ink2); margin-top:6px; text-align:center; }
#panel .glink { font-size:.85rem; margin-top:10px; }
#panel .glink a { color:var(--c-tatpurusa); text-decoration:none; border-bottom:1px dotted var(--c-tatpurusa); }
#panel .meta { font-size:.85rem; color:var(--ink2); margin-top:8px; }
#panel .note.est { font-style:italic; }
#panel .meta a { color:var(--c-tatpurusa); text-decoration:none; border-bottom:1px dotted var(--c-tatpurusa); }
#panel .numtag { color:var(--ink2); font-size:.8rem; letter-spacing:.02em; }
/* --- H8573 pilot: leaf numbers + one-legend corpus-share layer --- */
.num { font-weight:bold; opacity:.72; }
.fov { pointer-events:none; }
/* The share layer never invents a palette: it is the class hue, intensified.
   Band = opacity inside that hue; texture modes keep the same baseline. */
.fov.c-tatpurusa   { --fov:var(--c-tatpurusa); }
.fov.c-bahuvrihi   { --fov:var(--c-bahuvrihi); }
.fov.c-dvandva     { --fov:var(--c-dvandva); }
.fov.c-avyayibhava { --fov:var(--c-avyayibhava); }
#cakra.mode-light .fov[data-band=gte20]  { fill:var(--fov); fill-opacity:.96; }
#cakra.mode-light .fov[data-band="10to20"] { fill:var(--fov); fill-opacity:.84; }
#cakra.mode-light .fov[data-band="5to10"]  { fill:var(--fov); fill-opacity:.70; }
#cakra.mode-light .fov[data-band="1to5"]   { fill:var(--fov); fill-opacity:.54; }
#cakra.mode-light .fov[data-band=none]   { fill:var(--fov); fill-opacity:.16;
  stroke:var(--fov); stroke-width:1.5; stroke-dasharray:3 6; }
#cakra.mode-hatch .fov[data-band=gte20]  { fill:url(#pat-gte20); }
#cakra.mode-hatch .fov[data-band="10to20"] { fill:url(#pat-10to20); }
#cakra.mode-hatch .fov[data-band="5to10"]  { fill:url(#pat-5to10); }
#cakra.mode-hatch .fov[data-band="1to5"]   { fill:url(#pat-1to5); }
#cakra.mode-hatch .fov[data-band=none]   { fill:url(#pat-none); }
#cakra.mode-outline .fov[data-band=gte20]  { fill:none; stroke:var(--fov); stroke-width:8; }
#cakra.mode-outline .fov[data-band="10to20"] { fill:none; stroke:var(--fov); stroke-width:6; }
#cakra.mode-outline .fov[data-band="5to10"]  { fill:none; stroke:var(--fov); stroke-width:4; }
#cakra.mode-outline .fov[data-band="1to5"]   { fill:none; stroke:var(--fov); stroke-width:2.5; }
#cakra.mode-outline .fov[data-band=none]   { fill:none; stroke:var(--fov); stroke-width:2; stroke-dasharray:3 9; }
.freqbar { display:flex; gap:6px; align-items:center; flex-wrap:wrap; font-size:.85rem; width:100%; margin:0 0 6px; }
.freqbar button { font:inherit; font-size:.8rem; padding:3px 10px; border:1px solid var(--line);
  background:transparent; color:var(--ink2); border-radius:4px; cursor:pointer; }
.freqbar button.on { background:var(--ink); color:var(--surface); border-color:var(--ink); }
#bandlegend { display:flex; gap:14px; flex-wrap:wrap; font-size:.85rem; margin:0 0 8px; padding:0 2px; width:100%; }
#bandlegend span { display:inline-flex; align-items:center; gap:6px; }
#bandlegend i { width:14px; height:14px; border-radius:3px; display:inline-block; border:1px solid var(--line); background:transparent; }
body[data-freq=none] #bandlegend { display:none; }
/* legend swatches use the representative tatpuruṣa hue at the same intensities */
body[data-freq=light] #bandlegend i[data-band=gte20]  { background:#2a78d6; opacity:1; }
body[data-freq=light] #bandlegend i[data-band="10to20"] { background:#2a78d6; opacity:.84; }
body[data-freq=light] #bandlegend i[data-band="5to10"]  { background:#2a78d6; opacity:.70; }
body[data-freq=light] #bandlegend i[data-band="1to5"]   { background:#2a78d6; opacity:.54; }
body[data-freq=light] #bandlegend i[data-band=none]   { background:#2a78d6; opacity:.16; }
body[data-freq=hatch] #bandlegend i[data-band=gte20]  { background:repeating-linear-gradient(45deg,#4a4842 0 3px,transparent 3px 7px); }
body[data-freq=hatch] #bandlegend i[data-band="10to20"] { background:repeating-linear-gradient(45deg,#4a4842 0 2.5px,transparent 2.5px 7px); }
body[data-freq=hatch] #bandlegend i[data-band="5to10"]  { background:repeating-linear-gradient(45deg,#4a4842 0 2px,transparent 2px 7px); }
body[data-freq=hatch] #bandlegend i[data-band="1to5"]   { background:repeating-linear-gradient(45deg,#4a4842 0 1.5px,transparent 1.5px 7px); }
body[data-freq=hatch] #bandlegend i[data-band=none]   { background:repeating-linear-gradient(45deg,#9a978e 0 1px,transparent 1px 7px); }
body[data-freq=outline] #bandlegend i[data-band=gte20]  { border:4px solid #2a78d6; }
body[data-freq=outline] #bandlegend i[data-band="10to20"] { border:3px solid #2a78d6; }
body[data-freq=outline] #bandlegend i[data-band="5to10"]  { border:2px solid #2a78d6; }
body[data-freq=outline] #bandlegend i[data-band="1to5"]   { border:1px solid #2a78d6; }
body[data-freq=outline] #bandlegend i[data-band=none]   { border:1px dashed #2a78d6; }
.bandnote { color:var(--ink2); font-size:.78rem; width:100%; margin:0 2px 8px; }
.kevalachip { display:flex; align-items:center; gap:10px; font-size:.92rem; text-decoration:none;
  color:var(--ink); border:1px dashed var(--line); border-radius:6px; padding:7px 12px; margin:0 0 10px; width:100%;
  box-sizing:border-box; }
.kevalachip:hover { border-color:var(--ink2); }
.kevalachip b { font-weight:normal; border-bottom:1px dotted currentColor; }
.kevalachip span.goto { margin-left:auto; color:var(--ink2); font-size:.82rem; }
#legend { display:flex; gap:14px; flex-wrap:wrap; font-size:.9rem; margin:0 0 8px; padding:0 2px; width:100%; }
#legend span { display:inline-flex; align-items:center; gap:6px; }
#legend i { width:12px; height:12px; border-radius:3px; display:inline-block; }
.hint { color:var(--ink2); font-size:.8rem; width:100%; margin:2px 2px 0; }
/* --- embedded samāsa quiz: the wheel's own META is the question bank --- */
#quizbtn { font:inherit; font-size:.85rem; padding:3px 12px; border:1px solid var(--c-tatpurusa);
  background:var(--c-tatpurusa); color:#fff; border-radius:4px; cursor:pointer; }
#quiz { position:fixed; inset:0; z-index:50; background:rgba(0,0,0,.45); display:flex;
  align-items:center; justify-content:center; padding:16px; }
#quiz[hidden] { display:none; }
#quiz .qcard { background:var(--panel); color:var(--ink); border:1px solid var(--line);
  border-radius:8px; max-width:520px; width:100%; padding:20px 24px; box-shadow:0 8px 30px rgba(0,0,0,.25); }
#quiz h2 { margin:0 0 4px; font-size:1.25rem; font-weight:normal; }
#quiz .qsub { color:var(--ink2); font-size:.85rem; margin-bottom:12px; }
#quiz .qmodes { display:flex; gap:6px; margin-bottom:14px; flex-wrap:wrap; }
#quiz .qmodes button { font:inherit; font-size:.85rem; padding:4px 12px; border:1px solid var(--line);
  background:transparent; color:var(--ink2); border-radius:4px; cursor:pointer; }
#quiz .qmodes button.on { background:var(--ink); color:var(--surface); border-color:var(--ink); }
#quiz .qq { font-size:1.2rem; margin:8px 0 4px; }
#quiz .qq .pdeva { font-size:1rem; }
#quiz .qhint { color:var(--ink2); font-size:.9rem; margin:0 0 14px; }
#quiz .qopts { display:grid; gap:8px; }
#quiz .qopt { font:inherit; text-align:left; padding:9px 12px; border:1px solid var(--line);
  background:transparent; color:var(--ink); border-radius:5px; cursor:pointer; }
#quiz .qopt:hover { border-color:var(--ink2); }
#quiz .qopt.correct { border-color:#2d6a4f; background:rgba(45,106,79,.12); }
#quiz .qopt.wrong { border-color:#c0392b; background:rgba(192,57,43,.10); }
#quiz .qfb { margin-top:14px; font-size:.92rem; min-height:1.4em; }
#quiz .qfb a { color:var(--c-tatpurusa); }
#quiz .qnext { margin-top:12px; display:flex; gap:10px; justify-content:flex-end; }
#quiz .qnext button { font:inherit; font-size:.9rem; padding:6px 14px; border:1px solid var(--line);
  background:transparent; color:var(--ink); border-radius:4px; cursor:pointer; }
#quiz .qnext button.primary { background:var(--ink); color:var(--surface); }
</style>
</head>
<body>
<main>
<div id="wheelbox">__SVG__</div>
<aside id="panel">
  <h2>samāsa-cakra</h2>
  <div class="chain">колесо санскритских композитов</div>
  <div class="ru">Четыре класса по прадхана-схеме Патанджали, семейства и подтипы —
  по конспекту Э. З. Лейтана и правилам разбора (право-налево; двандва — единственное
  плоское исключение). Кликните сегмент.</div>
  <div class="rule">Источники: sanskrit-right-to-left-reading.md · KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md</div>
  <div class="panel-controls">
    <a class="repolink" href="https://github.com/gasyoun/SamasaChakram" target="_blank" rel="noopener" aria-label="Репозиторий на GitHub" title="Репозиторий на GitHub">
      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M12 .5C5.37.5 0 5.87 0 12.5c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.29-.01-1.05-.02-2.07-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.21.09 1.84 1.24 1.84 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.34-5.47-5.96 0-1.32.47-2.4 1.24-3.24-.13-.3-.54-1.53.12-3.19 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 016 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.25 2.89.12 3.19.77.84 1.23 1.92 1.23 3.24 0 4.63-2.8 5.65-5.48 5.95.43.37.81 1.1.81 2.22 0 1.6-.01 2.89-.01 3.28 0 .32.22.7.83.58A12.01 12.01 0 0024 12.5C24 5.87 18.63.5 12 .5z"/></svg>
      <span>GitHub</span>
    </a>
    <div id="legend">
      <span><i style="background:var(--c-tatpurusa)"></i>tatpuruṣa</span>
      <span><i style="background:var(--c-bahuvrihi)"></i>bahuvrīhi</span>
      <span><i style="background:var(--c-dvandva)"></i>dvandva</span>
      <span><i style="background:var(--c-avyayibhava)"></i>avyayībhāva</span>
      <button id="quizbtn" type="button">Квиз</button>
      <span id="scripttoggle"><button id="btn-iast" class="on">IAST</button><button id="btn-deva">देवनागरी</button></span>
    </div>
    <a class="kevalachip" href="#k=kevala" id="kevalachip">
      <span>§ 8 · <b>kevala-samāsa</b> — класс вне четырёх: отдельный вход</span>
      <span class="goto">карточка и задание →</span>
    </a>
    <div class="freqbar" role="group" aria-label="частотный слой">
      <span>Корпусная доля:</span>
      <button data-mode="none" class="on">без слоя</button>
      <button data-mode="light">светофор</button>
      <button data-mode="hatch">штриховка</button>
      <button data-mode="outline">контур</button>
    </div>
    <div id="bandlegend">__BANDLEGEND__</div>
    <p class="bandnote">__BANDNOTE__</p>
    <p class="hint">Колесо можно вращать (перетаскиванием); клик по сегменту — разбор справа; двойной клик — сброс поворота. Ссылка на карточку — <code>#k=&lt;id&gt;</code>.</p>
  </div>
</aside>
</main>
<div id="quiz" hidden role="dialog" aria-modal="true" aria-labelledby="quiz-title">
  <div class="qcard">
    <h2 id="quiz-title">Квиз по samaсам</h2>
    <div class="qsub">Вопросы из таксономии колеса · <span id="qscore">0 / 0</span></div>
    <div class="qmodes" role="group" aria-label="режим квиза">
      <button type="button" data-qmode="type" class="on">определи класс</button>
      <button type="button" data-qmode="vigraha">виграха → пример</button>
    </div>
    <div class="qq" id="qquest"></div>
    <p class="qhint" id="qhint"></p>
    <div class="qopts" id="qopts"></div>
    <div class="qfb" id="qfb" aria-live="polite"></div>
    <div class="qnext">
      <button type="button" id="qclose">закрыть</button>
      <button type="button" id="qnext" class="primary" hidden>дальше →</button>
    </div>
  </div>
</div>
<script>
const META = __META__;
const GAL = '__GAL__';
const svg = document.getElementById('cakra');
const wheel = document.getElementById('wheel');
const panel = document.getElementById('panel');
let rot = 0, dragging = false, a0 = 0, r0 = 0, moved = 0, downSeg = null, px = 0, py = 0;
function angleOf(ev) {
  const r = svg.getBoundingClientRect();
  const x = ev.clientX - (r.left + r.width/2), y = ev.clientY - (r.top + r.height/2);
  return Math.atan2(y, x) * 180 / Math.PI;
}
// The seg is remembered at pointerdown: once the pointer is captured the browser
// retargets the compat mouse events (click included) to the capture element, so a
// click handler reading ev.target would only ever see the <svg> itself.
svg.addEventListener('pointerdown', ev => {
  if (ev.button !== 0 && ev.pointerType === 'mouse') return;
  dragging = true; moved = 0; a0 = angleOf(ev); r0 = rot;
  px = ev.clientX; py = ev.clientY;
  downSeg = ev.target.closest ? ev.target.closest('.seg') : null;
  try { svg.setPointerCapture(ev.pointerId); } catch (e) {}
  ev.preventDefault();
});
function onMove(ev) {
  if (!dragging) return;
  const d = angleOf(ev) - a0;
  moved = Math.max(moved, Math.hypot(ev.clientX - px, ev.clientY - py));
  rot = r0 + d; wheel.setAttribute('transform', `rotate(${rot} 560 560)`);
}
function onUp(ev) {
  if (!dragging) return;
  dragging = false;
  if (moved <= 4 && downSeg) select(downSeg);   // a tap, not a drag
  downSeg = null;
}
// window-level so the drag survives a failed capture and a pointer leaving the svg
window.addEventListener('pointermove', onMove);
window.addEventListener('pointerup', onUp);
window.addEventListener('pointercancel', () => { dragging = false; downSeg = null; });
svg.addEventListener('dblclick', () => { rot = 0; wheel.setAttribute('transform', ''); });
document.getElementById('btn-iast').onclick = () => { document.body.classList.remove('deva');
  document.getElementById('btn-iast').classList.add('on'); document.getElementById('btn-deva').classList.remove('on'); };
document.getElementById('btn-deva').onclick = () => { document.body.classList.add('deva');
  document.getElementById('btn-deva').classList.add('on'); document.getElementById('btn-iast').classList.remove('on'); };
function select(seg) { openCard(seg.dataset.id, seg); }
function resolveId(id) { return ALIAS[id] || id; }
function openCard(rawId, seg) {
  const id = resolveId(rawId);
  const m = META[id]; if (!m) return false;
  document.querySelectorAll('.seg.sel').forEach(s => s.classList.remove('sel'));
  if (seg) seg.classList.add('sel');
  else { const t = document.querySelector(`.seg[data-id="${id}"]`); if (t) t.classList.add('sel'); }
  const num = m.n ? `<span class="numtag">№ ${m.n}</span> · ` : '';
  let h = `<h2>${num}${m.name}</h2><div class="chain">${m.class}${m.family ? ' · ' + m.family : ''}</div>`;
  if (m.ex) {
    h += `<div class="ex">${m.ex}</div><div class="vig">${m.vigraha}</div><div class="ru">«${m.ru}»</div>`;
    // Devanagari goes AFTER the translation, never interleaved with IAST
    // (MG ruling 25-11-2026): both lines together, each on its own row.
    const dv = [];
    if (m.ex_d && m.ex_d !== m.ex) dv.push(m.ex_d);
    if (m.vigraha_d && m.vigraha_d !== m.vigraha) dv.push(m.vigraha_d);
    if (dv.length) h += `<div class="pdeva">${dv.join('<br>')}</div>`;
  }
  if (m.kind === 'kevala') {
    if (m.context) h += `<div class="note">${m.context}</div>`;
    h += `<div class="rule">${m.rule}</div>`;
    if (m.second_ex) h += `<div class="note">${m.second_ex}</div>`;
  } else {
    h += `<div class="rule">${m.pradhana}<br>структура: ${m.structure}</div>`;
  }
  if (m.note) h += `<div class="note">${m.note}</div>`;
  if (m.freq) h += `<div class="note">${m.freq}</div>`;
  if (m.est) h += `<div class="note est">${m.est}</div>`;
  const links = [];
  (m.paras || []).forEach(pp => links.push(`<a href="${pp.href}">§ ${pp.num} в указателе параграфов</a>`));
  if (m.lesson) links.push(`<a href="${m.lesson.href}">${m.lesson.title}</a>`);
  if (m.kind === 'leaf') links.push(`<a href="${GAL}" target="_blank" rel="noopener">Галерея разобранных композитов</a>`);
  if (links.length) h += `<div class="glink">${links.join(' · ')}</div>`;
  if (m.diagram) h += `<figure class="diagram">${m.diagram}<figcaption>Klammerdiagramm — скобочная схема (композит с этой конструкцией из галереи)</figcaption></figure>`;
  h += `<div class="meta">Ссылка на карточку: <code>#k=${rawId}</code>${rawId !== id ? ' → ' + id : ''}</div>`;
  panel.innerHTML = h;
  return true;
}
// --- corpus-share layer: one legend, three encodings (H8573) ---
const MODES = ['none', 'light', 'hatch', 'outline'];
function setMode(mode) {
  MODES.forEach(m => cakra().classList.toggle('mode-' + m, m === mode));
  document.body.dataset.freq = mode;
  document.querySelectorAll('.freqbar button').forEach(b => b.classList.toggle('on', b.dataset.mode === mode));
}
function cakra() { return document.getElementById('cakra'); }
document.querySelectorAll('.freqbar button').forEach(b => { b.onclick = () => setMode(b.dataset.mode); });
// --- stable-id routing: #k=<leaf|family|class|kevala> (legacy ids resolve) ---
const ALIAS = __ALIAS__;
function route() {
  const h = decodeURIComponent(location.hash || '');
  const m = h.match(/^#k=(.+)$/);
  if (m) openCard(m[1], null);
}
window.addEventListener('hashchange', route);
setMode('none');
route();
// --- embedded quiz: the wheel's own META is the only question bank ---
const QUIZ_LEAVES = Object.entries(META).filter(([id, m]) =>
  m.kind === 'leaf' && m.ex && m.vigraha && m.ru);
const QUIZ_CLASSES = [...new Set(QUIZ_LEAVES.map(([id, m]) => m.class))];
const quizBox = document.getElementById('quiz');
let qMode = 'type', qCurrent = null, qLastId = null, qAsked = 0, qRight = 0, qLocked = false;
function shuffleQ(a) { const b = a.slice();
  for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; }
  return b; }
function pickLeaf() {
  let pool = QUIZ_LEAVES.filter(([id]) => id !== qLastId);
  if (!pool.length) pool = QUIZ_LEAVES;
  const [id, m] = pool[Math.floor(Math.random() * pool.length)];
  qLastId = id; return {id, m};
}
function devaSpan(iast, deva) { return (deva && deva !== iast) ? '<br><span class="pdeva">' + deva + '</span>' : ''; }
function nextQuestion() {
  const {id, m} = pickLeaf(); qCurrent = {id, m}; qLocked = false;
  document.getElementById('qnext').hidden = true;
  document.getElementById('qfb').textContent = '';
  const quest = document.getElementById('qquest'), hint = document.getElementById('qhint');
  let opts;
  if (qMode === 'type') {
    quest.innerHTML = m.ex + devaSpan(m.ex, m.ex_d);
    hint.textContent = '«' + m.ru + '» — к какому классу относится композит?';
    const wrong = QUIZ_CLASSES.filter(c => c !== m.class);
    opts = shuffleQ([m.class].concat(shuffleQ(wrong).slice(0, 3)))
      .map(c => ({label: c, correct: c === m.class}));
  } else {
    quest.innerHTML = m.vigraha + devaSpan(m.vigraha, m.vigraha_d);
    hint.textContent = 'Виграха сложного слова. Выберите соответствующий композит.';
    const pool = QUIZ_LEAVES.filter(([oid]) => oid !== id && META[oid].class !== m.class);
    const others = shuffleQ(pool).slice(0, 3).map(([oid, om]) => om.ex);
    opts = shuffleQ([m.ex].concat(others)).map(e => ({label: e, correct: e === m.ex}));
  }
  const box = document.getElementById('qopts'); box.innerHTML = '';
  opts.forEach(o => { const b = document.createElement('button'); b.type = 'button'; b.className = 'qopt';
    b.textContent = o.label; b.onclick = () => answerQ(o.correct, b); box.appendChild(b); });
}
function answerQ(correct, btn) {
  if (qLocked) return; qLocked = true; qAsked++; if (correct) qRight++;
  document.getElementById('qscore').textContent = qRight + ' / ' + qAsked;
  const m = qCurrent.m;
  btn.classList.add(correct ? 'correct' : 'wrong');
  const rightLabel = qMode === 'type' ? m.class : m.ex;
  if (!correct) document.querySelectorAll('.qopt').forEach(b => {
    if (b.textContent === rightLabel) b.classList.add('correct'); });
  const fb = document.getElementById('qfb');
  fb.innerHTML = (correct ? 'Верно. ' : 'Неверно. ') + 'Это <b>' + m.name + '</b> (' + m.class +
    (m.family ? ' · ' + m.family : '') + '). ' +
    '<a href="#k=' + qCurrent.id + '" id="qreveal">показать лепесток на колесе →</a>';
  document.getElementById('qreveal').onclick = () => { quizBox.hidden = true; };
  document.getElementById('qnext').hidden = false;
}
function openQuiz() { if (!QUIZ_LEAVES.length) return; quizBox.hidden = false; nextQuestion(); }
document.getElementById('quizbtn').onclick = openQuiz;
document.getElementById('qclose').onclick = () => { quizBox.hidden = true; };
document.getElementById('qnext').onclick = nextQuestion;
document.querySelectorAll('[data-qmode]').forEach(b => b.onclick = () => {
  qMode = b.dataset.qmode;
  document.querySelectorAll('[data-qmode]').forEach(x => x.classList.toggle('on', x === b));
  nextQuestion();
});
quizBox.addEventListener('click', ev => { if (ev.target === quizBox) quizBox.hidden = true; });
document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && !quizBox.hidden) quizBox.hidden = true; });
</script>
</body>
</html>
"""
BANDLEGEND = "".join(
    f'<span><i data-band="{b["id"]}"></i>{b["label"].replace("<", "&lt;")}</span>'
    for b in FREQ["bands"])
html = (html.replace("__B64__", b64).replace("__B64I__", b64i).replace("__B64D__", b64d)
        .replace("__GAL__", GALLERY_URL).replace("__META__", meta_json)
        .replace("__SVG__", svg_inline).replace("__ALIAS__", json.dumps(ALIAS, ensure_ascii=False))
        .replace("__BANDNOTE__", FREQ["band_note"]).replace("__BANDLEGEND__", BANDLEGEND))
with open(os.path.join(HERE, "samasacakra-wheel.html"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(html)
print("wrote samasacakra-wheel.html", len(html) // 1024, "KB;", total_leaves, "leaves")

# GitHub Pages copy (H1031): same page + SEO head, served from /docs
SEO = """<meta name="description" content="samāsa-cakra — интерактивное колесо санскритских композитов: 4 класса, 9 семейств, 58 подтипов с примерами и виграхами; IAST и деванагари; скобочные схемы Klammerdiagramm.">
<meta property="og:title" content="samāsa-cakra — колесо санскритских композитов">
<meta property="og:description" content="Интерактивная классификация санскритских сложных слов: вращающееся колесо, разбор каждого подтипа, скобочные схемы. Таксономия по конспекту Э. З. Лейтана.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://gasyoun.github.io/SamasaChakram/">
<meta property="og:site_name" content="SamasaChakram">
<link rel="canonical" href="https://gasyoun.github.io/SamasaChakram/">
"""
docs = os.path.join(HERE, "..", "docs")
os.makedirs(docs, exist_ok=True)
pages_html = html.replace('<meta name="viewport"', SEO + '<meta name="viewport"', 1)
with open(os.path.join(docs, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(pages_html)
open(os.path.join(docs, ".nojekyll"), "w").close()
print("wrote docs/index.html (GitHub Pages)")


# --- POSTER EXPORT (H1021, 16-07-2026) -------------------------------------
# A2 portrait (420x594 mm) single-sheet print: title in both scripts, the IAST
# wheel full-width, four class-rule panels, and the complete 58-subtype index
# (term - example IAST+Devanagari - RU gloss). Rendered to PDF via headless
# Edge --print-to-pdf (the @page rule pins the sheet size; fonts embed from
# the data-URI @font-face declarations).

cols = ""
for c in classes:
    n_c = sum(len(f["leaves"]) for f in c["families"])
    col = (f'<div class="col" style="border-color:{c["hue_light"]}">' 
           f'<h3>{c["name"]} · <span class="dv">{deva(c["name"])}</span></h3>'
           f'<div class="pp">{c["pradhana"]}</div>'
           f'<div class="pp"><b>структура:</b> {c["structure"]}</div>'
           f'<div class="pp muted">{n_c} подтипов</div>')
    for f in c["families"]:
        if len(c["families"]) > 1:
            col += f'<div class="fam">{f["name"]}</div>'
        for leaf in f["leaves"]:
            ex_d = deva(leaf["ex"])
            ex_d_html = f' <span class="dv">{ex_d}</span>' if ex_d != leaf["ex"] else ""
            col += (f'<div class="idx"><i style="background:{c["hue_light"]}"></i>'
                    f'<b>{leaf["term"]}</b> — {leaf["ex"]}{ex_d_html} — {leaf["ru"]}</div>')
    cols += col + "</div>"

poster_html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>samāsa-cakra — poster</title>
<style>
@font-face {{ font-family: 'Klammer Serif'; font-style: normal; src: url(data:font/woff2;base64,{b64}) format('woff2'); }}
@font-face {{ font-family: 'Klammer Serif'; font-style: italic; src: url(data:font/woff2;base64,{b64i}) format('woff2'); }}
@font-face {{ font-family: 'Klammer Deva'; src: url(data:font/woff2;base64,{b64d}) format('woff2'); }}
@page {{ size: 420mm 594mm; margin: 0; }}
html,body {{ margin:0; padding:0; width:420mm; height:594mm; background:#fcfcfb; color:#20201d;
  font-family:'Klammer Serif',Georgia,serif; overflow:hidden; }}
.sheet {{ width:420mm; height:593mm; box-sizing:border-box; padding:14mm 16mm 10mm;
  display:flex; flex-direction:column; overflow:hidden; }}
header {{ text-align:center; margin-bottom:2mm; }}
h1 {{ font-size:34pt; font-weight:normal; margin:0; letter-spacing:.02em; }}
h1 .dv {{ font-family:'Klammer Deva',serif; }}
.sub {{ font-size:10.5pt; color:#5d5c55; margin-top:1mm; }}
#wheelwrap {{ width:340mm; margin:0 auto; }}
#wheelwrap svg {{ width:100%; height:auto; display:block; }}
.l-deva {{ display:none; }}
.seg {{ stroke:#fcfcfb; stroke-width:2; }}
.fov {{ display:none; }}   /* H8573 share layer is screen-only */
.ring1 {{ fill-opacity:.50; }} .ring2 {{ fill-opacity:.30; }} .ring3 {{ fill-opacity:.16; }}
.c-tatpurusa {{ fill:#2a78d6; }} .c-bahuvrihi {{ fill:#1baf7a; }}
.c-dvandva {{ fill:#d99b00; }} .c-avyayibhava {{ fill:#b8a300; }}
.hub {{ fill:#fcfcfb; stroke:#ddd8cc; stroke-width:1.4; }}
.lbl {{ fill:#20201d; }} .lbl2r,.lbl3,.hublbl2 {{ fill:#5d5c55; }}
.cols {{ display:grid; grid-template-columns:repeat(4,1fr); gap:5mm; margin:3mm 0 0; flex:1; }}
.col {{ border-top:1.2mm solid; padding:2mm 1mm 0; }}
.col h3 {{ margin:0 0 1mm; font-size:12.5pt; font-weight:normal; }}
.col .dv {{ font-family:'Klammer Deva',serif; }}
.pp {{ font-size:8pt; line-height:1.35; color:#3c3a33; }}
.pp.muted {{ color:#8b887c; margin-bottom:1.5mm; }}
.fam {{ font-size:7.6pt; font-style:italic; color:#8b887c; margin:1.4mm 0 .4mm; }}
.idx {{ font-size:7.6pt; line-height:1.42; break-inside:avoid; margin-bottom:.6mm; }}
.idx i {{ display:inline-block; width:5pt; height:5pt; border-radius:1pt; margin-right:2pt; }}
.idx .dv {{ font-family:'Klammer Deva',serif; }}
footer {{ font-size:7.5pt; color:#8b887c; text-align:center; margin-top:2mm; }}
</style>
</head>
<body>
<div class="sheet">
<header>
  <h1>samāsa-cakra · <span class="dv">समास-चक्र</span></h1>
  <div class="sub">Колесо санскритских композитов — 4 класса · 10 семейств · 58 подтипов ·
  таксономия по конспекту Э. З. Лейтана («Сложные слова в санскрите»), структурные правила разбора MG
  (право-налево; двандва — единственное плоское исключение)</div>
</header>
<div id="wheelwrap">{svg_inline}</div>
<div class="cols">{cols}</div>
<footer>SamasaChakram · github.com/gasyoun/SamasaChakram · шрифты: Klammer Serif (Charis 7.000, SIL OFL) и
Klammer Deva (Noto Serif Devanagari, OFL) · Fable 5 (claude-fable-5) · 16-07-2026</footer>
</div>
</body>
</html>
"""
with open(os.path.join(HERE, "samasacakra-poster.html"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(poster_html)
print("wrote samasacakra-poster.html", len(poster_html) // 1024, "KB")
