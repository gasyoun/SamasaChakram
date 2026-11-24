#!/usr/bin/env python3
"""Build the H8573 five-lesson pilot pages: the web paragraph index and the five
lessons, from the conspectus DOCX and pilot_data.json.

    python samasacakra/build_pilot.py

Inputs (never hand-edited HTML):
  docs/SAMASA_Leitan_COMPLETE.docx   the main conspectus — every § heading and its
                                     title; the index is regenerated from it
  samasacakra/pilot_data.json        the five lessons, the corpus-share table and
                                     the kevala entry
Outputs:
  docs/paragrafy/index.html          paragraph index — one permanent anchor per §
  docs/uroki/index.html              pilot contents
  docs/uroki/<slug>.html             the five lessons

Design: reports/DRUMAM_WHEEL_DESIGN_24-11-2026.md (branch design/drumam-wheel).
"""
import os
import re
import sys
import json
import html
import docx

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
DOCX = os.path.join(DOCS, "SAMASA_Leitan_COMPLETE.docx")
PAGES = "https://gasyoun.github.io/SamasaChakram/"

PILOT = json.load(open(os.path.join(HERE, "pilot_data.json"), encoding="utf-8"))
TAX = json.load(open(os.path.join(HERE, "samasacakra-taxonomy.json"), encoding="utf-8"))
LESSONS = PILOT["lessons"]
LESSON_BY_LEAF = {l["leaf"]: l for l in LESSONS}
KEVALA = PILOT["kevala"]


def esc(t):
    return html.escape(t, quote=False)


def leaf_numbers():
    """The wheel's clockwise leaf number — same traversal as build_samasacakra.py."""
    out, n = {}, 0
    for c in TAX["classes"]:
        for f in c["families"]:
            for leaf in f["leaves"]:
                n += 1
                out[f'{c["id"]}--{f["id"]}--{leaf["id"]}'] = (n, leaf)
    return out


LEAVES = leaf_numbers()

# ---------------------------------------------------------------- conspectus
def read_conspectus():
    """Document-order sections: [(level, heading, [(num, title) ...])].

    Heading 1 is the class/preface level, Heading 2 the subsection level; a §
    belongs to the section it is printed under. Empty sections are kept — they
    carry the hierarchy ("II. BAHUVRĪHI") even when every § sits one level down.
    """
    d = docx.Document(DOCX)
    sections = [{"level": 0, "heading": None, "items": []}]
    seen = set()
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if p.style.name.startswith("Heading"):
            sections.append({"level": int(p.style.name.split()[-1]), "heading": t, "items": []})
            continue
        m = re.match(r"^§\s*(\d+(?:\.\d+)*)\.?\s*(.*)$", t)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            sections[-1]["items"].append((m.group(1), m.group(2).strip() or "—"))
    return [s for s in sections if s["heading"] or s["items"]]


def para_id(num):
    return "p-" + num.replace(".", "-")


def para_lessons(num):
    return [l for l in LESSONS if num in l["paras"]]


# ---------------------------------------------------------------- style
CSS = """
:root{--surface:#fcfcfb;--panel:#fff;--ink:#20201d;--ink2:#5d5c55;--line:#ddd8cc;
--blue:#2a78d6;--green:#2a7d4f;--amber:#d99b00;--red:#b8352a}
@media (prefers-color-scheme:dark){:root{--surface:#1a1a19;--panel:#232320;--ink:#f2efe6;
--ink2:#b5b2a5;--line:#3c3a33;--blue:#3987e5;--green:#37a06a;--amber:#c98500;--red:#d4614f}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--surface);color:var(--ink);
font-family:'Charis SIL',Charis,Georgia,'Times New Roman',serif;line-height:1.55}
main{max-width:920px;margin:0 auto;padding:24px 18px 64px}
a{color:var(--blue)}
h1{font-size:1.9rem;font-weight:normal;margin:.2em 0 .1em;line-height:1.2}
h2{font-size:1.15rem;font-weight:normal;margin:1.6em 0 .4em;letter-spacing:.01em}
.sub{color:var(--ink2);font-size:.95rem;margin:0 0 1.2em}
nav{display:flex;gap:14px;flex-wrap:wrap;font-size:.88rem;margin:0 0 18px;
border-bottom:1px solid var(--line);padding-bottom:10px}
nav a{text-decoration:none;border-bottom:1px dotted currentColor}
.lede{font-size:1.05rem;margin:0 0 1.2em}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin:0 0 18px}
.now{display:grid;grid-template-columns:1fr;gap:2px}
.now .vig{font-size:1.5rem;margin:.1em 0}
.now .gloss{color:var(--ink2);font-style:italic}
.now dl{margin:.6em 0 0;display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;font-size:.95rem}
.now dt{color:var(--ink2)}
.now dd{margin:0}
pre{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px;
overflow-x:auto;font-family:'Cascadia Mono',Consolas,'DejaVu Sans Mono',monospace;
font-size:.82rem;line-height:1.45}
details{border:1px solid var(--line);border-radius:6px;margin:0 0 10px;background:var(--panel)}
details summary{cursor:pointer;padding:9px 14px;font-size:.95rem}
details[open] summary{border-bottom:1px solid var(--line)}
details .inner{padding:12px 14px}
.src{color:var(--ink2);font-size:.8rem;margin:0 0 10px}
.exercise{margin:0 0 8px}
.exercise fieldset{border:1px solid var(--line);border-radius:6px;padding:12px 14px;margin:0}
.exercise legend{font-size:.9rem;color:var(--ink2);padding:0 6px}
.opt{display:block;margin:.35em 0;font-size:.96rem;cursor:pointer}
.opt input{margin-right:8px}
button.check{font:inherit;font-size:.9rem;padding:6px 16px;border:1px solid var(--line);
border-radius:5px;background:var(--panel);color:var(--ink);cursor:pointer;margin:10px 0 0}
button.check:hover{border-color:var(--ink2)}
.fb{margin:12px 0 0;font-size:.95rem;display:none}
.fb.show{display:block}
.fb .verdict{font-weight:bold}
.fb .ok{color:var(--green)}
.fb .bad{color:var(--red)}
.fb ul{margin:.5em 0 0;padding-left:1.2em;font-size:.9rem;color:var(--ink2)}
.fb li.ok b{color:var(--green)} .fb li.bad b{color:var(--red)}
.sources{font-size:.86rem;color:var(--ink2);margin:1.4em 0 0;padding-left:1.1em}
.sources li{margin:.25em 0}
.toc{list-style:none;padding:0;margin:0}
.toc li{border-bottom:1px solid var(--line);padding:10px 0}
.toc a{text-decoration:none;font-size:1.02rem}
.toc .why{color:var(--ink2);font-size:.86rem}
.idx{list-style:none;padding:0;margin:0}
.idx > li{border-bottom:1px solid var(--line);padding:7px 0;display:grid;
grid-template-columns:5.2em 1fr;gap:10px;align-items:baseline}
.idx .num{font-variant-numeric:tabular-nums;color:var(--ink2);font-size:.9rem}
.idx .num a{text-decoration:none;color:var(--ink2)}
.idx .links{font-size:.82rem;color:var(--ink2);display:block;margin-top:2px}
.idx .links a{color:var(--blue)}
.idx .links .muted{color:var(--ink2)}
h2.sec{margin-top:2em;border-top:2px solid var(--line);padding-top:.8em}
h3.sec2{margin:1.4em 0 .2em;font-size:1rem;font-weight:normal;color:var(--ink2)}
.filter{width:100%;font:inherit;padding:7px 10px;border:1px solid var(--line);
border-radius:5px;background:var(--panel);color:var(--ink);margin:0 0 14px}
.foot{margin-top:2.4em;border-top:1px solid var(--line);padding-top:12px;
color:var(--ink2);font-size:.82rem}
.neigh{display:flex;justify-content:space-between;gap:12px;font-size:.9rem;margin:1.6em 0 0}
"""


def head(title, extra=""):
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="Пилот SamasaChakram: пять сквозных уроков по санскритским композитам и веб-указатель параграфов конспекта Э. З. Лейтана.">
<style>{CSS}</style>
{extra}</head>
<body>
<main>
<nav>
  <a href="{PAGES}">← колесо</a>
  <a href="{PAGES}paragrafy/">указатель параграфов</a>
  <a href="{PAGES}uroki/">пять уроков</a>
  <a href="{PAGES}drumam/samasa_trainer.html">практика Drumam</a>
  <a href="../SAMASA_Leitan_COMPLETE.docx">конспект (DOCX)</a>
</nav>
"""


def foot(extra=""):
    return f"""<div class="foot">{extra}
Пилот H8573 · таксономия и § — конспект Э. З. Лейтана; структуры — Lowe 2015 (LFG),
формулы развёртки — Warnemyr; доли — Kulkarni &amp; Kumar 2013, таблица 5 и § 14 конспекта.
Собрано <code>samasacakra/build_pilot.py</code> из <code>pilot_data.json</code> —
правьте данные, а не этот файл.</div>
</main>
</body>
</html>
"""


# ---------------------------------------------------------------- paragraph index
def build_index():
    sections = read_conspectus()
    rows, total = [], 0
    for s in sections:
        if not s["heading"] and not s["items"]:
            continue
        if s["heading"]:
            lvl = "h2" if s["level"] <= 1 else "h3"
            cls = "sec" if lvl == "h2" else "sec2"
            rows.append(f'<{lvl} class="{cls}" id="sec-{re.sub(r"[^a-z0-9]+", "-", s["heading"].lower()).strip("-")[:40]}">'
                        f'{esc(s["heading"])}</{lvl}>')
        if not s["items"]:
            continue
        rows.append('<ul class="idx">')
        for num, title in s["items"]:
            total += 1
            les = para_lessons(num)
            links = []
            for l in les:
                links.append(f'<a href="{PAGES}uroki/{l["slug"]}.html">разбор: урок {l["n"]}</a>')
            if not links:
                links.append('<span class="muted">разбора в пилоте нет</span>')
            leaf = LESSON_BY_LEAF.get(next((l["leaf"] for l in les), ""), None)
            if leaf and leaf["leaf"] in LEAVES:
                n = LEAVES[leaf["leaf"]][0]
                links.append(f'<a href="{PAGES}#k={leaf["leaf"]}">лепесток № {n} на колесе</a>')
            rows.append(
                f'<li id="{para_id(num)}"><span class="num"><a href="#{para_id(num)}">§ {num}</a></span>'
                f'<span>{esc(title)}<span class="links">{" · ".join(links)}</span></span></li>')
        rows.append("</ul>")
    body = "".join(rows)
    html_out = head("Указатель параграфов — конспект Э. З. Лейтана") + f"""
<h1>Указатель параграфов</h1>
<p class="sub">Конспект Э. З. Лейтана, «Сложные слова в санскрите» — {total} параграфов.
У каждого § постоянный якорь, название, ссылка на связанный разбор (если он входит в пилот)
и на главный DOCX.</p>
<p class="lede">Ссылка на параграф выглядит так: <code>{PAGES}paragrafy/#p-4-1-1</code>.
Якорь не меняется при обновлении текста конспекта: он выводится из номера §, а не из порядка
абзацев. Ссылки на разборы ведут в пять уроков пилота; если разбора нет, это сказано прямо.</p>
<p class="lede"><a href="../SAMASA_Leitan_COMPLETE.docx">Главный DOCX конспекта</a> ·
<a href="{PAGES}">колесо</a> ·
<a href="{PAGES}uroki/">пять уроков</a></p>
<input class="filter" id="q" type="search" placeholder="фильтр по номеру или названию §">
{body}
""" + foot() + """
<script>
// progressive enhancement only: every row is fully readable without it
const q = document.getElementById('q');
q.addEventListener('input', () => {
  const v = q.value.trim().toLowerCase();
  document.querySelectorAll('.idx > li').forEach(li => {
    li.style.display = !v || li.textContent.toLowerCase().includes(v) ? '' : 'none';
  });
});
</script>
"""
    out = os.path.join(DOCS, "paragrafy")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html_out)
    print(f"wrote docs/paragrafy/index.html — {total} §§, {len(sections)} sections")
    return total


# ---------------------------------------------------------------- lessons
def render_diagrams(lesson):
    out = []
    for dg in lesson["diagrams"]:
        out.append(f"""<details>
<summary>{esc(dg['title'])}</summary>
<div class="inner">
<p class="src">модель: {esc(dg['model'])}<br>источник: {esc(dg['source'])}</p>
<pre>{esc(dg['content'])}</pre>
</div>
</details>""")
    return "\n".join(out)


def render_exercise(lesson):
    ex = lesson["exercise"]
    kind = ex["kind"]
    typ = "checkbox" if kind == "multi" else "radio"
    opts = "\n".join(
        f'<label class="opt"><input type="{typ}" name="z{ex["id"]}" value="{o["id"]}" '
        f'data-ok="{1 if o.get("ok") else 0}"> {esc(o["text"])}</label>'
        for o in ex["options"])
    why = "\n".join(
        f'<li class="{"ok" if o.get("ok") else "bad"}"><b>{esc(o["text"][:60])}{"…" if len(o["text"]) > 60 else ""}</b>'
        f'{"" if o.get("ok") else " — " + esc(o.get("why", ""))}</li>'
        for o in ex["options"])
    paras = " · ".join(f'<a href="{PAGES}paragrafy/#{para_id(p)}">§ {p}</a>' for p in lesson["paras"])
    return f"""<div class="exercise" id="zadanie">
<fieldset>
<legend>Задание к уроку {lesson['n']}</legend>
<p>{esc(ex["prompt"])}</p>
{opts}
<button class="check" data-kind="{kind}" data-ex="{ex["id"]}">Проверить</button>
<div class="fb" id="fb-{ex["id"]}">
  <p class="verdict" id="verdict-{ex["id"]}"></p>
  <p>{esc(ex["explanation"])}</p>
  <ul>{why}</ul>
  <p class="src">Разбор: {paras} · <a href="{PAGES}drumam/samasa_trainer.html">общий режим практики Drumam</a></p>
</div>
</fieldset>
</div>"""


EX_JS = """
document.querySelectorAll('button.check').forEach(btn => {
  btn.onclick = () => {
    const kind = btn.dataset.kind, ex = btn.dataset.ex;
    const box = document.getElementById('fb-' + ex);
    const picks = [...document.querySelectorAll(`input[name="z${ex}"]`)].filter(i => i.checked);
    const okPicks = picks.filter(i => i.dataset.ok === '1');
    const all = [...document.querySelectorAll(`input[name="z${ex}"]`)];
    const need = all.filter(i => i.dataset.ok === '1').map(i => i.value).sort().join(',');
    const got = picks.map(i => i.value).sort().join(',');
    let pass, msg;
    if (!picks.length) { pass = false; msg = 'Ничего не выбрано — отметьте вариант.'; }
    else if (kind === 'multi') {
      pass = got === need;
      msg = pass ? 'Принято: отмечены все допустимые разборы.'
                 : (okPicks.length === picks.length
                    ? 'Отмечены допустимые разборы, но не все: без контекста форма допускает ещё один.'
                    : 'Принято частично: отмечен вариант, который форма не подтверждает.');
    } else {
      pass = picks.length === 1 && okPicks.length === 1;
      msg = pass ? 'Верно.' : 'Неверно: см. объяснение ниже.';
    }
    const v = document.getElementById('verdict-' + ex);
    v.textContent = msg;
    v.className = 'verdict ' + (pass ? 'ok' : 'bad');
    box.classList.add('show');
  };
});
"""


def build_lesson(lesson):
    leaf_n = None
    if lesson["leaf"] in LEAVES:
        leaf_n = LEAVES[lesson["leaf"]][0]
    card_link = (f'<a href="{PAGES}#k={lesson["leaf"]}">карточка'
                 f'{" № " + str(leaf_n) if leaf_n else ""} на колесе</a>')
    ids = "\n".join(f'<div><dt>{esc(s["label"])}</dt><dd>{esc(s["text"])}</dd></div>'
                    for s in lesson["scheme"])
    body = "\n".join(f"<p>{esc(p)}</p>" for p in lesson["body"])
    srcs = "\n".join(f'<li><a href="{s["url"]}">{esc(s["label"])}</a></li>' for s in lesson["sources"])
    prev_l = LESSONS[lesson["n"] - 2] if lesson["n"] > 1 else None
    next_l = LESSONS[lesson["n"]] if lesson["n"] < len(LESSONS) else None
    neigh = ""
    if prev_l or next_l:
        left = f'<a href="{prev_l["slug"]}.html">← урок {prev_l["n"]}</a>' if prev_l else "<span></span>"
        right = f'<a href="{next_l["slug"]}.html">урок {next_l["n"]} →</a>' if next_l else "<span></span>"
        neigh = f'<div class="neigh">{left}{right}</div>'
    return head(f'Урок {lesson["n"]}. {lesson["title"]}') + f"""
<h1>{esc(lesson["title"])}</h1>
<p class="sub">{esc(lesson["subtitle"])}</p>
<p class="lede">{esc(lesson["source_locator"])} · {card_link}</p>

<section class="card now">
  <div class="vig">{esc(lesson["vigraha"]["form"])}</div>
  <div class="gloss">«{esc(lesson["vigraha"]["gloss"])}»</div>
  <p>{esc(lesson["vigraha"]["analysis"])}</p>
  <dl>{ids}</dl>
</section>

<h2>Разбор</h2>
{body}

<h2>Формальные схемы</h2>
<p class="src">Схемы раскрываются по запросу и подписаны: у каждой указана модель и источник.
Схемы Лоу даны учебным переложением, а не воспроизведением авторских рисунков.</p>
{render_diagrams(lesson)}

<h2>Задание Drumam</h2>
{render_exercise(lesson)}

<h2>Источники урока</h2>
<ul class="sources">{srcs}</ul>
{neigh}
""" + foot() + f"<script>{EX_JS}</script>"


def build_lessons():
    out = os.path.join(DOCS, "uroki")
    os.makedirs(out, exist_ok=True)
    for lesson in LESSONS:
        with open(os.path.join(out, f'{lesson["slug"]}.html'), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_lesson(lesson))
    items = []
    for l in LESSONS:
        leaf_n = LEAVES[l["leaf"]][0] if l["leaf"] in LEAVES else None
        tag = f'лепесток № {leaf_n}' if leaf_n else 'отдельный вход, § 8'
        items.append(f'<li><a href="{l["slug"]}.html">Урок {l["n"]}. {esc(l["title"])}</a>'
                     f'<span class="why"><br>{esc(l["subtitle"])} · {tag} · '
                     f'§ {", § ".join(l["paras"])}</span></li>')
    idx = head("Пять уроков пилота — SamasaChakram") + f"""
<h1>Пять уроков пилота</h1>
<p class="sub">Сквозные уроки по санскритским композитам: от одной формы до чтения текста.
В каждом — vigraha и учебная схема сразу, формальные схемы по запросу, задание Drumam
с объяснением и ссылкой на параграф конспекта.</p>
<p class="lede">Порядок задан сверкой конспекта и колеса: генитивная развёртка, вложенность,
неоднозначность, объединённый лепесток prathamā / ekadeśin и отдельный вход kevala-samāsa.
Полный выпуск требует литературного обзора по всем темам — здесь только пять уроков пилота.</p>
<ul class="toc">{"".join(items)}</ul>
<h2>Что дальше</h2>
<p class="lede">Разборы связаны с колесом устойчивыми идентификаторами
(<code>{PAGES}#k=&lt;id&gt;</code>), с указателем параграфов
(<a href="{PAGES}paragrafy/">постоянные якоря</a>) и с практикой
<a href="{PAGES}drumam/samasa_trainer.html">Drumam</a>. Из карточки на колесе открывается
тот же урок, из урока — та же карточка.</p>
""" + foot()
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(idx)
    print(f"wrote docs/uroki/ — index + {len(LESSONS)} lessons")


if __name__ == "__main__":
    n = build_index()
    build_lessons()
    print(f"pilot built: {len(LESSONS)} lessons, {n} § anchors")
