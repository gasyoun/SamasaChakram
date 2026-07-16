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
# Rings: hub "samāsa-cakra" · ring 1 = the four classes (Patañjali's pradhāna
# scheme) · ring 2 = families · ring 3 = leaf subtypes, one canonical example
# each (click for vigraha + RU gloss in the HTML). Angular width ∝ leaf count.
# Colors: the four validated categorical hues (dataviz palette, light+dark
# modes both validated); identity is never color-alone — every segment carries
# a direct ink label and 2px surface gaps separate all fills.
# Emits samasacakra-wheel.svg (static, light) and samasacakra-wheel.html
# (embedded Klammer Serif, dark mode, hover, click panel, drag-to-rotate).
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
WOFF2 = os.path.join(HERE, "..", "klammerdiagramm", "charis-klammer-subset.woff2")
WOFF2_DEVA = os.path.join(HERE, "noto-deva-klammer-subset.woff2")
FONT = "'Klammer Serif', 'Charis SIL', Charis, Georgia, serif"

def load_diagram(fname):
    # inline a Klammerdiagramm SVG for a leaf's detail panel. The plate SVGs are
    # fully currentColor (strokes + text + hatch), so they inherit the panel's
    # theme ink; the page already embeds Klammer Serif, which they reference.
    with open(os.path.join(HERE, "..", "klammerdiagramm", fname), encoding="utf-8") as fh:
        return fh.read()

CX = CY = 560
R_HUB, R1a, R1b, R2a, R2b, R3a, R3b = 96, 102, 186, 192, 288, 294, 448
GAP_DEG = 0.0          # gaps drawn as surface-color strokes, not angular gaps

T = json.load(open(os.path.join(HERE, "samasacakra-taxonomy.json"), encoding="utf-8"))
classes = T["classes"]
total_leaves = sum(len(f["leaves"]) for c in classes for f in c["families"])
UNIT = 360.0 / total_leaves

def pol(r, a_deg):
    a = math.radians(a_deg - 90)          # 0° at 12 o'clock, clockwise
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

def radial_label(r, a, text, size, cls):
    # text runs along the radius; flipped on the left half so it reads outward
    x, y = pol(r, a)
    rot = a - 90 if a % 360 <= 180 else a + 90
    anchor = "start" if a % 360 <= 180 else "end"
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" class="{cls}" '
            f'text-anchor="{anchor}" dominant-baseline="middle" '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">{text}</text>')

def tangential_label(r, a0, a1, text, size, cls):
    a = (a0 + a1) / 2
    x, y = pol(r, a)
    rot = a if 90 <= a % 360 <= 270 else a          # tangential; flip bottom half
    rot = a + 180 if 90 < a % 360 < 270 else a
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" class="{cls}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">{text}</text>')

svg, meta = [], {}
svg.append('<g id="wheel">')
a = 0.0
for c in classes:
    n_c = sum(len(f["leaves"]) for f in c["families"])
    span_c = n_c * UNIT
    svg.append(f'<path d="{arc_path(R1a, R1b, a, a + span_c)}" class="seg c-{c["id"]} ring1" data-id="{c["id"]}"/>')
    if span_c >= 36:
        svg.append(dual(tangential_label, (R1a + R1b) / 2, a, a + span_c, c["name"], 30, "lbl lbl1"))
    else:
        svg.append(dual(radial_label, R1a + 6, a + span_c / 2, c["name"], 19, "lbl lbl1"))
    meta[c["id"]] = {"kind": "class", "name": c["name"], "pradhana": c["pradhana"],
                     "structure": c["structure"], "class": c["name"], "cid": c["id"]}
    af = a
    for f in c["families"]:
        span_f = len(f["leaves"]) * UNIT
        fid = f'{c["id"]}--{f["id"]}'
        svg.append(f'<path d="{arc_path(R2a, R2b, af, af + span_f)}" class="seg c-{c["id"]} ring2" data-id="{fid}"/>')
        fname = f["name"]
        if span_f >= 24:
            svg.append(dual(tangential_label, (R2a + R2b) / 2, af, af + span_f, fname, 19, "lbl lbl2"))
        else:
            svg.append(dual(radial_label, R2a + 8, af + span_f / 2, fname, 15, "lbl lbl2r"))
        meta[fid] = {"kind": "family", "name": fname, "class": c["name"], "cid": c["id"],
                     "pradhana": c["pradhana"], "structure": c["structure"]}
        al = af
        for leaf in f["leaves"]:
            lid = f'{c["id"]}--{f["id"]}--{leaf["id"]}'
            svg.append(f'<path d="{arc_path(R3a, R3b, al, al + UNIT)}" class="seg c-{c["id"]} ring3" data-id="{lid}"/>')
            svg.append(dual(radial_label, R3a + 8, al + UNIT / 2, leaf["term"], 14.5, "lbl lbl3"))
            meta[lid] = {"kind": "leaf", "name": leaf["term"], "class": c["name"], "cid": c["id"],
                         "family": fname, "pradhana": c["pradhana"], "structure": c["structure"],
                         "ex": leaf["ex"], "vigraha": leaf["vigraha"], "ru": leaf["ru"],
                         "ex_d": deva(leaf["ex"]), "vigraha_d": deva(leaf["vigraha"]),
                         "note": leaf.get("note", ""),
                         "diagram": load_diagram(leaf["diagram"]) if leaf.get("diagram") else ""}
            al += UNIT
        af += span_f
    a += span_c

svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_HUB}" class="hub"/>')
svg.append(f'<text x="{CX}" y="{CY - 10}" font-size="34" class="lbl hublbl" text-anchor="middle">samāsa</text>')
svg.append(f'<text x="{CX}" y="{CY + 26}" font-size="20" class="lbl hublbl2" text-anchor="middle">cakra</text>')
svg.append(f'<text x="{CX}" y="{CY - 10}" font-size="34" class="lbl hublbl l-deva" text-anchor="middle">समास</text>')
svg.append(f'<text x="{CX}" y="{CY + 26}" font-size="20" class="lbl hublbl2 l-deva" text-anchor="middle">चक्र</text>')
svg.append('</g>')

STYLE_LIGHT = """
.seg { stroke: var(--surface); stroke-width: 2; cursor: pointer; }
.ring1 { fill-opacity: .50; } .ring2 { fill-opacity: .30; } .ring3 { fill-opacity: .16; }
.c-tatpurusa { fill: #2a78d6; } .c-bahuvrihi { fill: #1baf7a; }
.c-dvandva { fill: #eda100; } .c-avyayibhava { fill: #008300; }
.hub { fill: var(--surface); stroke: var(--line); stroke-width: 1.4; }
.lbl { fill: var(--ink); pointer-events: none; }
.lbl2r, .lbl3 { fill: var(--ink2); }
.hublbl2 { fill: var(--ink2); }
.seg:hover { fill-opacity: .72; }
.l-deva { display: none; }
"""

svg_doc = (f'<svg viewBox="0 0 {2*CX} {2*CY}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f"font-family=\"{FONT}\">"
           f'<title>samāsa-cakra</title>'
           f'<desc>The wheel of Sanskrit compounds: four classes, their families and leaf subtypes, '
           f'from the Leitan-crosswalked taxonomy with the MG structural rulings.</desc>'
           f'<style>:root {{ --surface:#fcfcfb; --ink:#20201d; --ink2:#5d5c55; --line:#ddd8cc; }}\n{STYLE_LIGHT}</style>'
           f'<rect width="100%" height="100%" fill="#fcfcfb"/>'
           + "".join(svg) + "</svg>")

with open(os.path.join(HERE, "samasacakra-wheel.svg"), "w", encoding="utf-8") as fh:
    fh.write(svg_doc)
print("wrote samasacakra-wheel.svg", len(svg_doc) // 1024, "KB")

b64 = base64.b64encode(open(WOFF2, "rb").read()).decode("ascii")
b64d = base64.b64encode(open(WOFF2_DEVA, "rb").read()).decode("ascii")
meta_json = json.dumps(meta, ensure_ascii=False)
# the inline SVG for HTML drops the internal <style>/<rect> (the page styles it)
svg_inline = ('<svg id="cakra" viewBox="0 0 1120 1120" role="img" '
              f"font-family=\"{FONT}\">" + "".join(svg) + "</svg>")

html = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>samāsa-cakra — колесо санскритских композитов</title>
<style>
@font-face { font-family: 'Klammer Serif'; src: url(data:font/woff2;base64,__B64__) format('woff2'); }
@font-face { font-family: 'Klammer Deva'; src: url(data:font/woff2;base64,__B64D__) format('woff2'); }
:root { --surface:#fcfcfb; --ink:#20201d; --ink2:#5d5c55; --line:#ddd8cc; --panel:#ffffff; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme=light]) { --surface:#1a1a19; --ink:#f2efe6; --ink2:#b5b2a5; --line:#3c3a33; --panel:#232320;
    --c-tatpurusa:#3987e5; --c-bahuvrihi:#199e70; --c-dvandva:#c98500; --c-avyayibhava:#008300; }
}
:root[data-theme=dark] { --surface:#1a1a19; --ink:#f2efe6; --ink2:#b5b2a5; --line:#3c3a33; --panel:#232320;
  --c-tatpurusa:#3987e5; --c-bahuvrihi:#199e70; --c-dvandva:#c98500; --c-avyayibhava:#008300; }
:root { --c-tatpurusa:#2a78d6; --c-bahuvrihi:#1baf7a; --c-dvandva:#eda100; --c-avyayibhava:#008300; }
html,body { margin:0; background:var(--surface); color:var(--ink); font-family:'Klammer Serif',Georgia,serif; }
main { max-width:1500px; margin:0 auto; padding:20px 16px; display:flex; gap:20px; flex-wrap:wrap; }
#wheelbox { flex:1 1 640px; min-width:340px; }
svg { display:block; width:100%; height:auto; touch-action:none; }
.seg { stroke:var(--surface); stroke-width:2; cursor:pointer; transition:fill-opacity .12s; }
.ring1 { fill-opacity:.50; } .ring2 { fill-opacity:.30; } .ring3 { fill-opacity:.16; }
.c-tatpurusa { fill:var(--c-tatpurusa); } .c-bahuvrihi { fill:var(--c-bahuvrihi); }
.c-dvandva { fill:var(--c-dvandva); } .c-avyayibhava { fill:var(--c-avyayibhava); }
.seg:hover, .seg.sel { fill-opacity:.74; }
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
#panel { flex:0 1 360px; min-width:300px; background:var(--panel); border:1px solid var(--line);
  border-radius:6px; padding:18px 20px; align-self:flex-start; position:sticky; top:16px; }
#panel h2 { margin:0 0 2px; font-size:1.3rem; font-weight:normal; }
#panel .chain { color:var(--ink2); font-size:.85rem; margin-bottom:10px; }
#panel .ex { font-size:1.15rem; margin:.5em 0 .1em; }
#panel .vig { color:var(--ink2); font-style:italic; }
#panel .ru { margin-top:.4em; }
#panel .rule,#panel .note { font-size:.85rem; color:var(--ink2); border-top:1px dashed var(--line);
  margin-top:12px; padding-top:8px; }
#panel .diagram { margin:12px 0 0; padding-top:10px; border-top:1px dashed var(--line); color:var(--ink); }
#panel .diagram svg { width:100%; height:auto; display:block; }
#panel .diagram figcaption { font-size:.78rem; color:var(--ink2); margin-top:6px; text-align:center; }
#legend { display:flex; gap:14px; flex-wrap:wrap; font-size:.9rem; margin:0 0 8px; padding:0 2px; width:100%; }
#legend span { display:inline-flex; align-items:center; gap:6px; }
#legend i { width:12px; height:12px; border-radius:3px; display:inline-block; }
.hint { color:var(--ink2); font-size:.8rem; width:100%; margin:2px 2px 0; }
</style>
</head>
<body>
<main>
<div id="legend">
  <span><i style="background:var(--c-tatpurusa)"></i>tatpuruṣa</span>
  <span><i style="background:var(--c-bahuvrihi)"></i>bahuvrīhi</span>
  <span><i style="background:var(--c-dvandva)"></i>dvandva</span>
  <span><i style="background:var(--c-avyayibhava)"></i>avyayībhāva</span>
  <span id="scripttoggle"><button id="btn-iast" class="on">IAST</button><button id="btn-deva">देवनागरी</button></span>
</div>
<p class="hint">Колесо можно вращать (перетаскиванием); клик по сегменту — разбор справа; двойной клик — сброс поворота.</p>
<div id="wheelbox">__SVG__</div>
<aside id="panel">
  <h2>samāsa-cakra</h2>
  <div class="chain">колесо санскритских композитов</div>
  <div class="ru">Четыре класса по прадхана-схеме Патанджали, семейства и подтипы —
  по конспекту Э. З. Лейтана и правилам разбора (право-налево; двандва — единственное
  плоское исключение). Кликните сегмент.</div>
  <div class="rule">Источники: sanskrit-right-to-left-reading.md · KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md</div>
</aside>
</main>
<script>
const META = __META__;
const svg = document.getElementById('cakra');
const wheel = document.getElementById('wheel');
const panel = document.getElementById('panel');
let rot = 0, dragging = false, a0 = 0, r0 = 0, moved = 0;
function angleOf(ev) {
  const r = svg.getBoundingClientRect();
  const x = ev.clientX - (r.left + r.width/2), y = ev.clientY - (r.top + r.height/2);
  return Math.atan2(y, x) * 180 / Math.PI;
}
svg.addEventListener('pointerdown', ev => { dragging = true; moved = 0; a0 = angleOf(ev); r0 = rot; svg.setPointerCapture(ev.pointerId); });
svg.addEventListener('pointermove', ev => { if (!dragging) return;
  const d = angleOf(ev) - a0; moved = Math.max(moved, Math.abs(d));
  rot = r0 + d; wheel.setAttribute('transform', `rotate(${rot} 560 560)`); });
svg.addEventListener('pointerup', () => { dragging = false; });
svg.addEventListener('dblclick', () => { rot = 0; wheel.setAttribute('transform', ''); });
document.getElementById('btn-iast').onclick = () => { document.body.classList.remove('deva');
  document.getElementById('btn-iast').classList.add('on'); document.getElementById('btn-deva').classList.remove('on'); };
document.getElementById('btn-deva').onclick = () => { document.body.classList.add('deva');
  document.getElementById('btn-deva').classList.add('on'); document.getElementById('btn-iast').classList.remove('on'); };
svg.addEventListener('click', ev => {
  if (moved > 3) return;                       // it was a drag, not a click
  const seg = ev.target.closest('.seg'); if (!seg) return;
  document.querySelectorAll('.seg.sel').forEach(s => s.classList.remove('sel'));
  seg.classList.add('sel');
  const m = META[seg.dataset.id]; if (!m) return;
  let h = `<h2>${m.name}</h2><div class="chain">${m.class}${m.family ? ' · ' + m.family : ''}</div>`;
  if (m.ex) h += `<div class="ex">${m.ex}</div><div class="pdeva">${m.ex_d}</div><div class="vig">${m.vigraha}${m.vigraha_d && m.vigraha_d !== m.vigraha ? ' · <span class="pdeva">' + m.vigraha_d + '</span>' : ''}</div><div class="ru">«${m.ru}»</div>`;
  h += `<div class="rule">${m.pradhana}<br>структура: ${m.structure}</div>`;
  if (m.note) h += `<div class="note">${m.note}</div>`;
  if (m.diagram) h += `<figure class="diagram">${m.diagram}<figcaption>Klammerdiagramm — скобочная схема этого композита</figcaption></figure>`;
  panel.innerHTML = h;
});
</script>
</body>
</html>
"""
html = html.replace("__B64__", b64).replace("__B64D__", b64d).replace("__META__", meta_json).replace("__SVG__", svg_inline)
with open(os.path.join(HERE, "samasacakra-wheel.html"), "w", encoding="utf-8") as fh:
    fh.write(html)
print("wrote samasacakra-wheel.html", len(html) // 1024, "KB;", total_leaves, "leaves")
