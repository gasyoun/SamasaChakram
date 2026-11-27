"""Build docs/samasa-indexes.html — the public Russian indexes page (H8638).

Two equally prominent indexes on one page:

  1. Указатель классификации — the canonical taxonomy from
     samasacakra-taxonomy.json: 4 classes / 9 families / 58 leaf subtypes in
     wheel-clockwise order, each row carrying the same stable id the wheel
     routes (#k=<id>), plus kevala-samāsa outside the four classes.

  2. Указатель материалов — only PUBLISHED materials of the estate that cover
     samāsa (live Pages pages, the kosha drills, the repo's own gallery blob).
     The csl-guides quiz once listed in docs/SAMASA_KNOWLEDGE_HUB.md §2 is a
     404 with no such page or repo content (verified 27-11-2026) — it is
     deliberately absent, and DEAD_QUIZ_URL below guards that absence.

Type <-> material links are ONE evidence model projected both ways:

  * kind "example" (◆) — a proven subtype example: the material names this
    exact leaf (a pilot lesson, a § of the conspectus reached by that lesson,
    or a Klammerdiagramm plate named in the taxonomy JSON itself);
  * kind "family" (◇) — a family/class-level relation: the material covers
    the class as a whole without naming any particular leaf.

Every edge is emitted twice — as a chip on the type row and as a back-chip in
the material card — so the two directions cannot drift; the pytest suite
(samasacakra/top1000/tests/test_indexes_page.py) verifies reciprocity, anchor
uniqueness, taxonomy completeness and the published-target allowlist on the
committed output.

Stdlib only; Python 3.11+: rerun with `python samasacakra/build_samasa_indexes.py`.
"""

import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")

PAGES = "https://gasyoun.github.io/SamasaChakram/"
BLOB = "https://github.com/gasyoun/SamasaChakram/blob/main/"
GALLERY = BLOB + "klammerdiagramm-worked-examples.md"
KOSHA_DRILLS = "https://gasyoun.github.io/kosha/reading/samasa/drills/"

# Negative control (see module docstring): must never appear on the page.
DEAD_QUIZ_URL = "https://sanskrit-lexicon.github.io/csl-guides/docs/users/samasa-quiz"

KEVALA_ID = "kevala"
REL_D1_ID = "d1"
REL_D1_A = "tatpurusa--dvigu"
REL_D1_B = "tatpurusa--karmadharaya"

# (id, title, url, venue, evidence) — class-level materials.
CLASS_LEVEL_MATERIALS = [
    ("wheel", "Колесо samāsa-cakra", PAGES,
     "страница Pages этого репозитория (генератор build_samasacakra.py)",
     "колесо и есть каноническая классификационная поверхность; карточка "
     "каждого типа открывается по #k=<id>"),
    ("paragrafy", "Указатель параграфов — 67 §§ конспекта", PAGES + "paragrafy/",
     "docs/paragrafy/index.html (Pages)",
     "все параграфы конспекта Лейтана с якорями #p-<n>; вход в первоисточник "
     "по номеру §"),
    ("drumam-tree", "Дерево решений Drumam", PAGES + "drumam/",
     "drumam/ + docs/drumam/ (Pages)",
     "пошаговый разбор композита справа-налево по четырём классам "
     "прадхана-схемы; SAMASA_KNOWLEDGE_HUB.md §1"),
    ("drumam-trainer", "Тренажёр Drumam", PAGES + "drumam/samasa_trainer.html",
     "docs/drumam/samasa_trainer.html (Pages)",
     "практика разбора по дереву решений; SAMASA_KNOWLEDGE_HUB.md §1"),
    ("kosha-drills", "Тренажёр kosha: identify + split", KOSHA_DRILLS,
     "внешний репозиторий kosha",
     "3 865 упражнений: определить класс и разложить композит (gold Гиты + "
     "корпус DCS); живая страница проверена 27-11-2026; "
     "SAMASA_KNOWLEDGE_HUB.md §2"),
    ("leitan", "Конспект Э. З. Лейтан (DOCX)", BLOB + "docs/SAMASA_Leitan_COMPLETE.docx",
     "docs/SAMASA_Leitan_COMPLETE.docx (репозиторий)",
     "первоисточник таксономии: полный конспект; главный источник при "
     "расхождениях — ADR 0001"),
    ("method-doc", "Метод чтения справа-налево", BLOB + "sanskrit-right-to-left-reading.md",
     "sanskrit-right-to-left-reading.md (репозиторий)",
     "канонический метод и решения MG о направлении — общее основание "
     "разбора любого композита"),
]

# Example-level material with its own card: its edges name concrete leaves
# (пластина per leaf from the taxonomy JSON diagram field), so it must NOT
# emit class-level "covers the whole class" edges.
GALLERY_MATERIAL = ("gallery", "Галерея Klammerdiagramm — скобочные схемы", GALLERY,
                    "20 пластин: скобочная схема разобранного композита с "
                    "виграхой; пластина лепестка доказывает пример именно "
                    "этого подтипа",
                    "klammerdiagramm-worked-examples.md; поле diagram лепестков "
                    "в samasacakra-taxonomy.json")

ALL_MATERIALS = CLASS_LEVEL_MATERIALS + [GALLERY_MATERIAL]

# Chip label of each material on the type side.
SHORT_MAT = {
    "wheel": "колесо",
    "paragrafy": "указатель §§",
    "drumam-tree": "дерево Drumam",
    "drumam-trainer": "тренажёр Drumam",
    "kosha-drills": "drills kosha",
    "leitan": "конспект DOCX",
    "method-doc": "метод справа-налево",
    "gallery": "пластина",
}

RELATION_D1 = {
    "id": REL_D1_ID,
    "a": REL_D1_A,
    "b": REL_D1_B,
    "note": ("семейство-уровневое отношение (D1): Лейтан помещает двигу как "
             "подтип кармадхараи (числительное на первом месте, три условия "
             "Панини); колесо оставляет двигу отдельным семейством — отношение "
             "показано здесь, а не как проверенный пример"),
    "source": "KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md, голосование D1",
}


# ---------------------------------------------------------------------------
# Evidence model
# ---------------------------------------------------------------------------

def load_json(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def build_edges(tax, pilot):
    """Every type<->material edge exactly once; both projections derive.

    Edge: {tp, mat, kind: example|family, detail, href}. `detail` is shown in
    both projections; `href` is the published target the material card cites.
    """
    edges = []

    for l in sorted(pilot["lessons"], key=lambda x: x["slug"]):
        num = l["slug"].split("-")[0]
        mid = "uroki-" + num
        url = PAGES + "uroki/" + l["slug"] + ".html"
        tp = l["leaf"]
        edges.append({"tp": tp, "mat": mid, "kind": "example",
                      "detail": "урок " + num, "href": url})
        for p in l["paras"]:
            edges.append({"tp": tp, "mat": "paragrafy", "kind": "example",
                          "detail": "§ " + p,
                          "href": PAGES + "paragrafy/#p-" + p.replace(".", "-")})

    # Gallery plates: the taxonomy JSON itself names the plate per leaf —
    # the most direct proven-subtype-example evidence there is.
    for c in tax["classes"]:
        for f in c["families"]:
            for leaf in f["leaves"]:
                dg = leaf.get("diagram")
                if not dg:
                    continue
                plates = [dg] if isinstance(dg, str) else dg
                edges.append({
                    "tp": c["id"] + "--" + f["id"] + "--" + leaf["id"],
                    "mat": "gallery", "kind": "example",
                    "detail": "пластина: " + ", ".join(plates), "href": GALLERY})

    # kevala: its own wheel card + conspectus § 8 (lesson 05 edges above).
    edges.append({"tp": KEVALA_ID, "mat": "wheel", "kind": "example",
                  "detail": "карточка kevala-samāsa", "href": PAGES + "#k=kevala"})

    # Class-level coverage: every class-level material covers all 4 classes.
    for mid, *_rest in CLASS_LEVEL_MATERIALS:
        for c in tax["classes"]:
            edges.append({"tp": c["id"], "mat": mid, "kind": "family",
                          "detail": None, "href": None})
    return edges


def build_model():
    tax = load_json("samasacakra-taxonomy.json")
    pilot = load_json("pilot_data.json")
    edges = build_edges(tax, pilot)
    leaves = []
    for c in tax["classes"]:
        for f in c["families"]:
            for leaf in f["leaves"]:
                leaves.append({
                    "id": c["id"] + "--" + f["id"] + "--" + leaf["id"],
                    "leaf": leaf, "class": c, "family": f})
    return {
        "tax": tax,
        "pilot": pilot,
        "edges": edges,
        "n_classes": len(tax["classes"]),
        "n_families": sum(len(c["families"]) for c in tax["classes"]),
        "n_leaves": len(leaves),
        "leaves": leaves,
        "materials": ALL_MATERIALS,
        "relation_d1": RELATION_D1,
        "kevala": pilot["kevala"],
        "aliases": pilot["legacy_leaf_aliases"],
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def e(s):
    return html.escape(str(s), quote=True)


def type_edge_chips(edges_of_tp):
    if not edges_of_tp:
        return ""
    parts = ['<span class="chips">']
    for ed in edges_of_tp:
        if ed["mat"].startswith("uroki-"):
            label = ed["detail"]                      # "урок 01"
        elif ed["mat"] == "paragrafy" and ed["detail"]:
            label = ed["detail"]                      # "§ 4.1.6"
        else:
            label = SHORT_MAT[ed["mat"]]
        cls = "chip example" if ed["kind"] == "example" else "chip"
        marker = "◆ " if ed["kind"] == "example" else "◇ "
        parts.append(
            f'<a class="{cls}" data-kind="{ed["kind"]}" data-tp="{ed["tp"]}" '
            f'data-mat="{ed["mat"]}" href="#mat-{ed["mat"]}">'
            f'{e(marker + label)}</a>')
    parts.append("</span>")
    return "".join(parts)


def material_back_chips(edges_of_mat, tax):
    if not edges_of_mat:
        return ""
    parts = ['<span class="chips">']
    for ed in edges_of_mat:
        label = short_tp(ed["tp"], tax)
        if ed["detail"] and ed["kind"] == "example":
            label += " — " + ed["detail"]
        cls = "chip example" if ed["kind"] == "example" else "chip"
        parts.append(
            f'<a class="{cls}" data-kind="{ed["kind"]}" data-tp="{ed["tp"]}" '
            f'data-mat="{ed["mat"]}" href="#tp-{ed["tp"]}">{e(label)}</a>')
    parts.append("</span>")
    return "".join(parts)


def short_tp(tp, tax):
    """Human chip label for a type id."""
    if tp == KEVALA_ID:
        return "kevala-samāsa"
    for c in tax["classes"]:
        if c["id"] == tp:
            return c["name"]
        for f in c["families"]:
            if c["id"] + "--" + f["id"] == tp:
                return f["name"]
            for leaf in f["leaves"]:
                if c["id"] + "--" + f["id"] + "--" + leaf["id"] == tp:
                    return leaf["term"]
    return tp


def render(model):
    tax = model["tax"]
    edges = model["edges"]

    edges_by_tp = {}
    edges_by_mat = {}
    for ed in edges:
        edges_by_tp.setdefault(ed["tp"], []).append(ed)
        edges_by_mat.setdefault(ed["mat"], []).append(ed)

    lesson_mats = sorted(model["pilot"]["lessons"], key=lambda x: x["slug"])
    mats_by_id = {m[0]: m for m in model["materials"]}

    out = []
    w = out.append
    w('<!doctype html>')
    w('<html lang="ru">')
    w('<head>')
    w('<meta charset="utf-8">')
    w('<meta name="viewport" content="width=device-width, initial-scale=1">')
    w('<title>samāsa — указатели: классификация и материалы</title>')
    w('<meta name="description" content="Перекрёстные указатели по санскритским '
      'сложным словам: классификация (4 класса, 9 семейств, 58 лепестков-подтипов '
      'с примерами и виграхами) и опубликованные материалы (уроки, §§ конспекта, '
      'пластины, тренажёры, drills), связанные двусторонними обоснованными '
      'ссылками.">')
    w('<link rel="canonical" href="' + e(PAGES + "samasa-indexes.html") + '">')
    w('<style>')
    w(':root { --surface:#fcfcfb; --ink:#20201d; --ink2:#5d5c55; --line:#ddd8cc;'
      ' --panel:#ffffff; --accent:#2a78d6;'
      ' --c-tatpurusa:#2a78d6; --c-bahuvrihi:#1baf7a; --c-dvandva:#d99b00;'
      ' --c-avyayibhava:#b8a300; }')
    w('@media (prefers-color-scheme: dark) { :root { --surface:#1a1a19;'
      ' --ink:#f2efe6; --ink2:#b5b2a5; --line:#3c3a33; --panel:#232320;'
      ' --c-tatpurusa:#3987e5; --c-bahuvrihi:#199e70; --c-dvandva:#e0b33c;'
      ' --c-avyayibhava:#c8b84a; } }')
    w('html,body { margin:0; background:var(--surface); color:var(--ink);'
      ' font-family:"Charis SIL",Charis,Georgia,"Noto Serif",serif;'
      ' line-height:1.45; font-size:16px; }')
    w('header { padding:18px 16px 6px; max-width:1500px; margin:0 auto; }')
    w('h1 { font-size:1.5rem; font-weight:normal; margin:0 0 2px; }')
    w('.sub { color:var(--ink2); margin:0 0 10px; }')
    w('.switch { display:flex; gap:8px; flex-wrap:wrap; margin:0 0 4px; }')
    w('.switch a { font-size:.92rem; text-decoration:none; color:var(--ink);'
      ' border:1px solid var(--line); border-radius:5px; padding:5px 12px;'
      ' background:var(--panel); }')
    w('.switch a:hover { border-color:var(--ink2); }')
    w('main.indexes { max-width:1500px; margin:0 auto; padding:10px 16px 28px;'
      ' display:grid; gap:22px; grid-template-columns:1fr; }')
    w('@media (min-width: 980px) { main.indexes { grid-template-columns:1fr 1fr;'
      ' align-items:start; } }')
    w('section h2 { font-size:1.25rem; font-weight:normal; margin:0;'
      ' border-bottom:2px solid var(--line); padding-bottom:6px; }')
    w('.count { color:var(--ink2); font-size:.88rem; margin:6px 0 12px; }')
    w('.cls { border:1px solid var(--line); border-radius:6px;'
      ' background:var(--panel); padding:12px 14px; margin:0 0 14px; }')
    w('.clsname { margin:0; font-size:1.12rem; font-weight:normal;'
      ' display:flex; align-items:center; gap:8px; flex-wrap:wrap; }')
    w('.dot { width:13px; height:13px; border-radius:3px; flex:none;'
      ' display:inline-block; }')
    w('.clsname a { color:inherit; text-decoration:none;'
      ' border-bottom:1px dotted var(--ink2); }')
    w('.clsline { color:var(--ink2); font-size:.85rem; margin:4px 0 8px; }')
    w('.fam { border-top:1px dashed var(--line); padding:8px 0 2px; }')
    w('.famname { font-size:1rem; margin:0 0 2px; }')
    w('.famname .famwheel a { font-size:.78rem; color:var(--accent);'
      ' text-decoration:none; white-space:nowrap; }')
    w('.famname .rel { display:block; font-size:.82rem; color:var(--ink2);'
      ' font-weight:normal; margin:2px 0 4px; }')
    w('.leaf { display:flex; gap:8px; align-items:baseline; flex-wrap:wrap;'
      ' padding:3px 0 3px 14px; font-size:.95rem; }')
    w('.leaf .no { color:var(--ink2); font-size:.78rem; flex:none; }')
    w('.leaf b { font-weight:normal; }')
    w('.leaf b a { color:inherit; text-decoration:none;'
      ' border-bottom:1px dotted var(--ink2); }')
    w('.leaf .ex { font-style:italic; }')
    w('.leaf .ru, .leaf .vig { color:var(--ink2); }')
    w('.leaf .note { color:var(--ink2); font-size:.82rem; }')
    w('.chips { display:inline-flex; gap:5px; flex-wrap:wrap; }')
    w('.chip { font-size:.75rem; line-height:1.2; text-decoration:none;'
      ' border:1px solid var(--line); border-radius:4px; padding:3px 7px;'
      ' color:var(--ink2); background:var(--surface); white-space:nowrap;'
      ' overflow-wrap:anywhere; }')
    w('a.chip:hover { color:var(--ink); border-color:var(--ink2); }')
    w('a.chip.example { border-color:var(--accent); color:var(--accent); }')
    w('span.chip.example { border-color:var(--accent); color:var(--accent); }')
    w('.mat { border:1px solid var(--line); border-radius:6px;'
      ' background:var(--panel); padding:12px 14px; margin:0 0 14px; }')
    w('.mat h3 { margin:0 0 2px; font-size:1.05rem; font-weight:normal; }')
    w('.mat h3 a { color:var(--accent); text-decoration:none;'
      ' border-bottom:1px dotted var(--accent); overflow-wrap:anywhere; }')
    w('.mat .venue { color:var(--ink2); font-size:.82rem; margin:2px 0 6px; }')
    w('.mat .ev { font-size:.82rem; color:var(--ink2); border-top:1px dashed'
      ' var(--line); margin:8px 0 0; padding-top:6px; }')
    w('.mat .cov { font-size:.88rem; margin:6px 0 0; }')
    w('.mat .cov .lbl { color:var(--ink2); font-size:.78rem; display:block;'
      ' margin:6px 0 2px; }')
    w('.backtop { font-size:.8rem; color:var(--ink2); text-decoration:none;'
      ' display:inline-block; margin-top:6px; }')
    w('.kevala { border:1px dashed var(--line); border-radius:6px;'
      ' padding:10px 14px; font-size:.95rem; }')
    w('footer { max-width:1500px; margin:0 auto; padding:6px 16px 26px;'
      ' color:var(--ink2); font-size:.8rem; }')
    w('footer code { overflow-wrap:anywhere; }')
    w('</style>')
    w('</head>')
    w('<body>')
    w('<header>')
    w('<h1>samāsa — указатели: классификация и материалы</h1>')
    w('<p class="sub">Два равноправных указателя по сложным словам санскрита: '
      'каноническая таксономия колеса и всё опубликованное вокруг неё, '
      'связанные двусторонними ссылками. Маркер чипа различает связи: '
      '<span class="chip example">◆ пример</span> — проверенный пример подтипа '
      '(урок, § конспекта или пластина, называющие именно этот лепесток); '
      '<span class="chip">◇ уровень класса</span> — материал покрывает класс '
      'целиком, без доказательства каждого лепестка.</p>')
    w('<nav class="switch" aria-label="переход между указателями">')
    w('<a href="#classification">Указатель классификации</a>')
    w('<a href="#materials">Указатель материалов</a>')
    w('<a href="' + e(PAGES) + '">Колесо samāsa-cakra ↗</a>')
    w('</nav>')
    w('</header>')
    w('<main class="indexes">')

    # ================= classification index =================
    w('<section id="classification" aria-labelledby="classification-h">')
    w('<h2 id="classification-h">Указатель классификации</h2>')
    w(f'<p class="count">{model["n_classes"]} класса · {model["n_families"]} '
      f'семейства · {model["n_leaves"]} лепестков-подтипов, плюс kevala-samāsa '
      'вне четырёх классов. Порядок строк — по часовой стрелке колеса, № '
      'лепестков совпадают с номерами на колесе; каждый заголовок открывает '
      'свой тип на колесе.</p>')

    no = 0
    for c in tax["classes"]:
        w('<article class="cls" id="tp-' + c["id"] + '">')
        w(f'<h3 class="clsname"><span class="dot" style="background:var(--c-{c["id"]})"></span>'
          f'{e(c["name"])} '
          f'<a href="{e(PAGES + "#k=" + c["id"])}" title="открыть класс на колесе">на колесе ↗</a>'
          + type_edge_chips(edges_by_tp.get(c["id"], [])) + '</h3>')
        w(f'<p class="clsline">{e(c["pradhana"])} · {e(c["structure"])}</p>')
        for f in c["families"]:
            fid = c["id"] + "--" + f["id"]
            w('<div class="fam" id="tp-' + fid + '">')
            w('<h4 class="famname">' + e(f["name"]))
            if fid == REL_D1_A:
                w(f'<span class="rel" id="rel-{REL_D1_ID}-a">⟶ '
                  f'{e(model["relation_d1"]["note"])} Основание: '
                  f'{e(model["relation_d1"]["source"])}; обратная сторона — '
                  f'<a href="#rel-{REL_D1_ID}-b">karmadhāraya</a>.</span>')
            if fid == REL_D1_B:
                w(f'<span class="rel" id="rel-{REL_D1_ID}-b">⟵ обратная сторона '
                  f'отношения D1: семейство двигу связано с кармадхараи '
                  f'<a href="#rel-{REL_D1_ID}-a">на уровне семейств</a>. '
                  f'Основание: {e(model["relation_d1"]["source"])}.</span>')
            w(f'<span class="famwheel"><a href="{e(PAGES + "#k=" + fid)}" '
              f'title="открыть семейство на колесе">на колесе ↗</a></span>')
            w('</h4>')
            for leaf in f["leaves"]:
                no += 1
                lid = c["id"] + "--" + f["id"] + "--" + leaf["id"]
                legacy = ""
                if leaf.get("legacy_ids"):
                    legacy = (' <span class="ru">(бывший идентификатор «'
                              + e(", ".join(leaf["legacy_ids"]))
                              + '» ведёт в эту же карточку)</span>')
                w(f'<div class="leaf" id="tp-{lid}">'
                  f'<span class="no">№ {no}</span>'
                  f'<b><a href="{e(PAGES + "#k=" + lid)}">{e(leaf["term"])}</a></b> — '
                  f'<span class="ex">{e(leaf["ex"])}</span> · '
                  f'<span class="vig">{e(leaf["vigraha"])}</span> · '
                  f'<span class="ru">«{e(leaf["ru"])}»</span>{legacy} '
                  + type_edge_chips(edges_by_tp.get(lid, []))
                  + '</div>')
                if leaf.get("note"):
                    w('<div class="leaf"><span class="no"></span>'
                      '<span class="note">' + e("Примечание: " + leaf["note"])
                      + '</span></div>')
            w('</div>')
        w('</article>')

    k = model["kevala"]
    w('<article class="kevala" id="tp-' + KEVALA_ID + '">')
    w('<b>' + e(k["title"]) + '</b> — вне четырёх классов (не входит в счёт '
      'лепестков; отдельная карточка рядом с колесом): '
      '<span class="ex">' + e(k["card"]["ex"]) + '</span> · '
      '<span class="ru">«' + e(k["card"]["ru"]) + '»</span> '
      '<a href="' + e(PAGES + "#k=kevala") + '">карточка на колесе ↗</a> '
      + type_edge_chips(edges_by_tp.get(KEVALA_ID, [])))
    w('</article>')
    w('</section>')

    # ================= materials index =================
    w('<section id="materials" aria-labelledby="materials-h">')
    w('<h2 id="materials-h">Указатель материалов</h2>')
    total_mats = len(model["materials"]) + len(lesson_mats)
    w(f'<p class="count">{total_mats} опубликованных материалов; каждая ссылка '
      'ведёт на живую опубликованную страницу, а чипы покрытия возвращают в '
      'указатель классификации — те же связи, что и у типов, в обратную '
      'сторону.</p>')

    order = (["wheel"]
             + ["uroki-" + l["slug"].split("-")[0] for l in lesson_mats]
             + [m[0] for m in model["materials"] if m[0] != "wheel"])
    for mid in order:
        if mid.startswith("uroki-"):
            l = next(x for x in lesson_mats
                     if "uroki-" + x["slug"].split("-")[0] == mid)
            title = l["title"]
            url = PAGES + "uroki/" + l["slug"] + ".html"
            venue = "урок пилота (docs/uroki/, Pages)"
            ev = ("разбирает свой лепесток таксономии целиком; параграфы "
                  "конспекта — из pilot_data.json")
        else:
            _, title, url, venue, ev = mats_by_id[mid]
        w('<article class="mat" id="mat-' + mid + '">')
        w('<h3><a href="' + e(url) + '" rel="noopener">' + e(title) + ' ↗</a></h3>')
        w('<p class="venue">' + e(venue) + '</p>')
        cov = edges_by_mat.get(mid, [])
        examples = [ed for ed in cov if ed["kind"] == "example"]
        fams = [ed for ed in cov if ed["kind"] == "family"]
        if examples:
            w('<p class="cov"><span class="lbl">Проверенные примеры '
              '(◆, доказаны уроком, § конспекта или пластиной):</span>'
              + material_back_chips(examples, tax) + '</p>')
        if mid == "paragrafy":
            sec_hrefs = sorted({e["href"] for e in cov if e["href"]})
            if sec_hrefs:
                w('<p class="cov"><span class="lbl">Прямые ссылки на §§ '
                  '(опубликованные якоря указателя):</span><span class="chips">')
                for h in sec_hrefs:
                    label = "§ " + h.rsplit("#p-", 1)[1].replace("-", ".")
                    w(f'<a class="chip" href="{e(h)}" rel="noopener">{e(label)}</a>')
                w('</span></p>')
        if fams:
            w('<p class="cov"><span class="lbl">Отношение уровня класса '
              '(◇, материал покрывает класс целиком, без конкретных '
              'лепестков):</span>' + material_back_chips(fams, tax) + '</p>')
        w('<p class="ev">Основание: ' + e(ev) + '.</p>')
        w('<a class="backtop" href="#classification">↑ к классификации</a>')
        w('</article>')
    w('</section>')
    w('</main>')
    w('<footer>')
    w('Сгенерировано <code>samasacakra/build_samasa_indexes.py</code> из '
      '<code>samasacakra/samasacakra-taxonomy.json</code> + '
      '<code>samasacakra/pilot_data.json</code>; страницу не правят руками — '
      'перегенерируют: <code>python samasacakra/build_samasa_indexes.py</code>. '
      'Таксономия — конспект Э. З. Лейтан (ADR 0001). Партнёрская страница: '
      '<a href="' + e(PAGES) + '">колесо samāsa-cakra</a>.')
    w('</footer>')
    w('</body>')
    w('</html>')
    return "\n".join(out) + "\n"


_MODEL = {}


def _model():
    global _MODEL
    if not _MODEL:
        _MODEL = build_model()
    return _MODEL


def main():
    model = _model()
    doc = render(model)
    os.makedirs(DOCS, exist_ok=True)
    out = os.path.join(DOCS, "samasa-indexes.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    print("wrote docs/samasa-indexes.html", len(doc) // 1024, "KB;",
          model["n_classes"], "classes,", model["n_families"], "families,",
          model["n_leaves"], "leaves,", len(model["edges"]), "edges,",
          len(model["materials"]) + len(model["pilot"]["lessons"]), "materials")


if __name__ == "__main__":
    main()
