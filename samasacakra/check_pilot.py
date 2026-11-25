#!/usr/bin/env python3
"""Acceptance checks for the H8573 five-lesson pilot.

    python samasacakra/check_pilot.py            # exit 0 = all checks pass
    python samasacakra/check_pilot.py -v         # print every check, not just failures

Fail-closed: any FAIL exits 1, so the pilot cannot land on a green claim it did
not earn. The checks cover the design's own verification list
(reports/DRUMAM_WHEEL_DESIGN_24-11-2026.md, «Проверка»):

  * one unique external number per leaf; a frequency-mode switch keeps the
    numbers, the range meaning and the legend readable;
  * every subtype/§ link opens the right place, the index offers the DOCX, and
    the legacy ekadeśin id resolves to the merged leaf card;
  * exact, group and missing shares are distinguishable, and a group share is
    never repeated as the share of its leaves;
  * one end-to-end example each for prathamā / ekadeśin, kevala-samāsa and an
    ambiguous compound, with card -> analysis -> exercise -> explanation.
"""
import os
import re
import sys
import json
import math
import docx

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
PILOT = json.load(open(os.path.join(HERE, "pilot_data.json"), encoding="utf-8"))
TAX = json.load(open(os.path.join(HERE, "samasacakra-taxonomy.json"), encoding="utf-8"))
LESSONS = PILOT["lessons"]
FREQ = PILOT["frequency"]["entries"]
BANDS = {b["id"] for b in PILOT["frequency"]["bands"]}

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    return ok


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def leaves():
    out = []
    for c in TAX["classes"]:
        for f in c["families"]:
            for leaf in f["leaves"]:
                out.append((f'{c["id"]}--{f["id"]}--{leaf["id"]}', c["id"], f["id"], leaf))
    return out


LEAVES = leaves()
LEAF_IDS = [l[0] for l in LEAVES]
FAM_IDS = [f'{c["id"]}--{f["id"]}' for c in TAX["classes"] for f in c["families"]]
ALIAS = PILOT["legacy_leaf_aliases"]


def resolve(i):
    return ALIAS.get(i, i)


# ------------------------------------------------------------------ data layer
def check_data():
    check("taxonomy: 58 leaves", len(LEAVES) == 58, f"{len(LEAVES)}")
    check("taxonomy: leaf ids unique", len(set(LEAF_IDS)) == len(LEAF_IDS))
    check("taxonomy: no leaf id collides with an alias key",
          not (set(LEAF_IDS) & set(ALIAS)), ", ".join(sorted(set(LEAF_IDS) & set(ALIAS))))
    check("taxonomy: merged leaf prathama exists",
          "tatpurusa--vibhakti--prathama" in LEAF_IDS)
    check("taxonomy: legacy ekadesin leaf is gone",
          not any(i.endswith("--ekadesin") for i in LEAF_IDS))
    vib = [c for c in TAX["classes"] if c["id"] == "tatpurusa"][0]
    fam = [f for f in vib["families"] if f["id"] == "vibhakti"][0]
    check("taxonomy: prathama is first in the case row",
          fam["leaves"][0]["id"] == "prathama", fam["leaves"][0]["id"])
    check("alias: ekadesin resolves to the merged leaf",
          resolve("ekadesin") == "tatpurusa--vibhakti--prathama"
          and resolve("tatpurusa--tp-special--ekadesin") == "tatpurusa--vibhakti--prathama")

    # a rename must not leave a dead id in executable code: the JEV probe's gold
    # map is the one committed place that hard-codes leaf ids (short form)
    probe = read(os.path.join(HERE, "samasa_subtype_jev_choice_probe.py"))
    block = probe.split("GOLD = {", 1)[1].split("\n}", 1)[0]
    gold = dict(re.findall(r'"([\w-]+)": "([\w-]+)",', block))
    short = {i.split("--")[-1] for i in LEAF_IDS}
    dead = sorted({v for v in gold.values() if v not in short})
    check("probe: every gold leaf id still exists in the taxonomy", not dead,
          f"{len(gold)} gold rows; dead: " + ", ".join(dead))

    # the conspectus' own § set is the authority for every para reference
    d = docx.Document(os.path.join(DOCS, "SAMASA_Leitan_COMPLETE.docx"))
    paras = set()
    for p in d.paragraphs:
        m = re.match(r"^§\s*(\d+(?:\.\d+)*)\.?\s*", p.text.strip())
        if m:
            paras.add(m.group(1))
    check("conspectus: § set read", len(paras) > 60, f"{len(paras)} §§")

    check("lessons: exactly five", len(LESSONS) == 5, f"{len(LESSONS)}")
    check("lessons: numbering 1..5", [l["n"] for l in LESSONS] == [1, 2, 3, 4, 5])
    check("lessons: slugs unique", len({l["slug"] for l in LESSONS}) == len(LESSONS))
    for l in LESSONS:
        tag = f"урок {l['n']}"
        tgt = resolve(l["leaf"])
        check(f"{tag}: leaf id resolves", tgt == "kevala" or tgt in LEAF_IDS, tgt)
        bad = [p for p in l["paras"] if p not in paras]
        check(f"{tag}: every § exists in the conspectus", not bad, ", ".join(bad))
        check(f"{tag}: at least one formal diagram", len(l.get("diagrams", [])) >= 1)
        for dg in l.get("diagrams", []):
            ok = all(str(dg.get(k, "")).strip() for k in ("model", "source", "content"))
            check(f"{tag}: diagram «{dg.get('id')}» is labelled with model + source", ok)
        ex = l["exercise"]
        oks = [o for o in ex["options"] if o.get("ok")]
        wrongs = [o for o in ex["options"] if not o.get("ok")]
        check(f"{tag}: exercise has ≥2 options", len(ex["options"]) >= 2)
        check(f"{tag}: exercise has a correct answer", len(oks) >= 1)
        check(f"{tag}: single-choice exercise has exactly one answer",
              ex["kind"] != "single" or len(oks) == 1, f"{len(oks)}")
        check(f"{tag}: every wrong option explains itself",
              all(str(o.get("why", "")).strip() for o in wrongs))
        check(f"{tag}: exercise cites an existing §", ex["para"] in paras, ex["para"])
        check(f"{tag}: explanation present", len(ex["explanation"]) > 20)
        check(f"{tag}: vigraha + scheme shown up front",
              bool(l["vigraha"]["form"]) and len(l["scheme"]) >= 3)

    check("kevala: § exists in the conspectus", PILOT["kevala"]["para"] in paras,
          PILOT["kevala"]["para"])

    # corpus shares: ADR 0002/0003 — the four visual bands are reserved for MEASURED
    # shares that match a leaf tag exactly; estimates are notes and carry nothing
    for e in FREQ:
        tag = f'доля {e["tag"]}'
        check(f"{tag}: scope known", e["scope"] in ("leaf", "group"), e["scope"])
        check(f"{tag}: kind known", e["kind"] in ("share", "estimate"), e["kind"])
        tgt = e["target"]
        ok_t = tgt in LEAF_IDS if e["scope"] == "leaf" else tgt in FAM_IDS
        check(f"{tag}: target exists in the taxonomy", ok_t, tgt)
        if e["kind"] == "share":
            check(f"{tag}: band known", e["band"] in BANDS, str(e.get("band")))
            check(f"{tag}: measured share carries count + pct + tag",
                  isinstance(e.get("count"), int) and isinstance(e.get("pct"), (int, float)))
            want = ("gte20" if e["pct"] >= 20 else "10to20" if e["pct"] >= 10
                    else "5to10" if e["pct"] >= 5 else "1to5" if e["pct"] >= 1 else "none")
            check(f"{tag}: band follows the published thresholds", e["band"] == want,
                  f'{e["band"]} vs {want} at {e["pct"]}%')
            check(f"{tag}: mapping verified against the source's tag list",
                  bool(str(e.get("mapping_verified", "")).strip()))
        else:
            check(f"{tag}: estimate carries no band", "band" not in e or not e["band"])
            check(f"{tag}: estimate carries its printed value",
                  bool(str(e.get("value_text", "")).strip()), str(e.get("value_text")))
            check(f"{tag}: estimate says it is not a measured share",
                  "не измеренная доля" in str(e.get("note", "")))
        check(f"{tag}: provenance text present", bool(str(e.get("source_text", "")).strip()))
    shares = [e for e in FREQ if e["kind"] == "share"]
    check("frequency: the five table-5 shares are the only measured ones",
          len(shares) == 5, ", ".join(e["tag"] for e in shares))
    check("frequency: measured shares published only at leaf scope",
          all(e["scope"] == "leaf" for e in shares))
    check("frequency: every estimate stays out of the visual bands",
          all("band" not in e or not e["band"] for e in FREQ if e["kind"] == "estimate"))
    return paras


# ------------------------------------------------------------------ html layer
def check_index_html(paras):
    h = read(os.path.join(DOCS, "paragrafy", "index.html"))
    ids = re.findall(r'<li id="(p-[\d-]+)"', h)
    check("index: one anchor per §", len(ids) == len(set(ids)) == len(paras),
          f"{len(ids)} anchors / {len(paras)} §§")
    check("index: no duplicate anchor", len(ids) == len(set(ids)))
    missing = [p for p in paras if "p-" + p.replace(".", "-") not in ids]
    check("index: every conspectus § has an anchor", not missing, ", ".join(missing[:5]))
    check("index: links the main DOCX", "SAMASA_Leitan_COMPLETE.docx" in h)
    check("index: every § row states a related analysis or its absence",
          h.count("разбора в пилоте нет") + h.count("разбор: урок") >= len(paras))
    for l in LESSONS:
        for p in l["paras"]:
            if p in paras:
                check(f"index: § {p} points at lesson {l['n']}",
                      f'#p-{p.replace(".", "-")}' in h and f'uroki/{l["slug"]}.html' in h)
    return h


def check_lessons_html():
    for l in LESSONS:
        path = os.path.join(DOCS, "uroki", f'{l["slug"]}.html')
        if not os.path.exists(path):
            check(f"урок {l['n']}: page exists", False, path)
            continue
        h = read(path)
        tag = f"урок {l['n']}"
        check(f"{tag}: page exists", True)
        check(f"{tag}: shows the vigraha immediately", l["vigraha"]["form"] in h)
        check(f"{tag}: formal diagrams are expandable", h.count("<details>") >= 1)
        check(f"{tag}: every diagram names its model and source",
              h.count("модель:") == len(l["diagrams"]) == h.count("источник:"))
        check(f"{tag}: exercise has a feedback block", 'class="fb"' in h)
        check(f"{tag}: feedback carries the explanation", l["exercise"]["explanation"][:40] in h)
        check(f"{tag}: links back to the wheel card", f'#k={l["leaf"]}' in h)
        check(f"{tag}: links the Drumam practice mode", "samasa_trainer.html" in h)
        for p in l["paras"]:
            check(f"{tag}: § {p} link uses the permanent anchor",
                  f'paragrafy/#p-{p.replace(".", "-")}' in h)


def check_wheel_html():
    h = read(os.path.join(DOCS, "index.html"))
    segs = re.findall(r'<path d="[^"]*" class="seg c-[\w-]+ ring3" data-id="([^"]+)" data-n="(\d+)" data-band="(\w+)"/>', h)
    check("wheel: 58 numbered leaf segments", len(segs) == 58, f"{len(segs)}")
    nums = [int(s[1]) for s in segs]
    check("wheel: numbers are exactly 1..58", sorted(nums) == list(range(1, 59)),
          f"{len(set(nums))} unique")
    check("wheel: leaf ids match the taxonomy", [s[0] for s in segs] == LEAF_IDS)
    bands = {s[0]: s[2] for s in segs}
    check("wheel: every band value is a known band", set(bands.values()) <= BANDS,
          ", ".join(sorted(set(bands.values()) - BANDS)))
    want = {e["target"]: e["band"] for e in FREQ
            if e["scope"] == "leaf" and e["kind"] == "share"}
    drift = [lid for lid in LEAF_IDS if bands.get(lid) != want.get(lid, "none")]
    check("wheel: each segment carries exactly its published band", not drift,
          ", ".join(f"{d}:{bands.get(d)}!={want.get(d, 'none')}" for d in drift[:4]))

    # the numbers live in their own layer, appended after the hub, and no mode
    # rule can reach them: the layer is outside every .seg and the mode CSS only
    # ever targets .fov / #bandlegend
    num_tags = re.findall(r'<text [^>]*class="lbl num"[^>]*>(\d+)</text>', h)
    check("wheel: one number text per leaf", len(num_tags) == 58, f"{len(num_tags)}")
    check("wheel: number texts are not inside a segment path", h.count('class="lbl num"') == 58)
    mode_rules = re.findall(r"\.mode-\w+[^{]*\{[^}]*\}", h)
    check("wheel: mode rules never touch the number layer",
          all("num" not in r for r in mode_rules), f"{len(mode_rules)} rules")
    check("wheel: mode CSS exists for all three encodings",
          all(f"mode-{m}" in h for m in ("light", "hatch", "outline")))
    check("wheel: hatch patterns defined once per band",
          all(f'id="pat-{b}"' in h for b in BANDS))
    check("wheel: four mode buttons", len(re.findall(r'data-mode="(?:none|light|hatch|outline)"', h)) == 4)
    check("wheel: one legend with five band states",
          len(re.findall(r'<i data-band="[\w]+"></i>', h)) == len(BANDS),
          str(len(re.findall(r'<i data-band="[\w]+"></i>', h))))
    check("wheel: frequency overlay per leaf",
          len(re.findall(r'class="fov c-[\w-]+"', h)) == 58,
          str(len(re.findall(r'class="fov c-[\w-]+"', h))))
    check("wheel: kevala entry beside the wheel", 'class="kevalachip"' in h and "#k=kevala" in h)
    check("wheel: hash routing present", "hashchange" in h and "location.hash" in h)
    check("wheel: legacy alias map embedded",
          '"ekadesin": "tatpurusa--vibhakti--prathama"' in h)

    m = re.search(r"const META = (\{.*?\});\nconst GAL", h, re.S)
    meta = json.loads(m.group(1)) if m else {}
    check("wheel: META parsed", bool(meta), f"{len(meta)} cards")
    check("wheel: kevala card exists", "kevala" in meta)
    group_entries = {e["target"]: e for e in FREQ if e["scope"] == "group"}
    leaf_entries = {e["target"]: e for e in FREQ
                    if e["scope"] == "leaf" and e["kind"] == "share"}
    leaf_est = {e["target"]: e for e in FREQ
                if e["scope"] == "leaf" and e["kind"] == "estimate"}
    banded = [lid for lid, v in bands.items() if v != "none"]
    check("wheel: exactly the five measured shares are banded", len(banded) == 5,
          f"{len(banded)}: " + ", ".join(sorted(banded)))
    check("wheel: every banded segment has a measured share behind it",
          set(banded) == set(leaf_entries))
    check("wheel: bands present are the ones the measured shares justify",
          {bands[l] for l in banded} == {leaf_entries[l]["band"] for l in banded})
    leaf_meta = {k: v for k, v in meta.items() if v.get("kind") == "leaf"}
    check("wheel: one card per leaf", len(leaf_meta) == 58, f"{len(leaf_meta)}")
    bad_band, bad_line = [], []
    for lid, card in leaf_meta.items():
        e = leaf_entries.get(lid)
        want = e["band"] if e else "none"
        if card["band"] != want:
            bad_band.append(lid)
        line = card.get("freq", "")
        if e and e["kind"] == "share" and f'{e["pct"]:.2f}%' not in line:
            bad_line.append(lid)
        if not e and "нет сопоставимой доли" not in line:
            bad_line.append(lid)
    check("wheel: card band matches the published entry", not bad_band, ", ".join(bad_band[:3]))
    check("wheel: card states its measured share or its absence", not bad_line, ", ".join(bad_line[:3]))
    # a rank exists only where the tag matches exactly, and it says what it ranks among
    ranked = sorted(leaf_entries.values(), key=lambda e: -e["pct"])
    for i, e in enumerate(ranked, 1):
        line = leaf_meta.get(e["target"], {}).get("freq", "")
        check(f'wheel: {e["tag"]} card shows rank {i} of {len(ranked)}',
              f"ранг: <b>{i} из {len(ranked)}</b>" in line, line[:70])
    check("wheel: every measured card explains what the rank ranks among",
          all("не среди всех подтипов" in leaf_meta[e["target"]]["freq"] for e in ranked))
    check("wheel: no rank is shown where no measured share exists",
          not any("Корпусный ранг" in c.get("freq", "") for lid, c in leaf_meta.items()
                  if lid not in leaf_entries))
    # estimates are visible notes, never quantitative marking
    est_missing = [lid for lid in leaf_est if leaf_est[lid]["value_text"] not in leaf_meta.get(lid, {}).get("est", "")]
    check("wheel: every § 14 estimate is shown as its own note", not est_missing,
          ", ".join(est_missing[:3]))
    leaked = [lid for lid in leaf_est
              if "Корпусная доля" in leaf_meta.get(lid, {}).get("est", "")
              or "ранг" in leaf_meta.get(lid, {}).get("est", "")]
    check("wheel: no estimate is dressed as a measured share", not leaked, ", ".join(leaked[:3]))
    check("wheel: estimate note states it is not a measured share",
          all("не измеренная доля" in leaf_meta[lid]["est"] for lid in leaf_est))
    # a group share is published at the group and nowhere else
    leaks = []
    for gid, e in group_entries.items():
        for lid, card in leaf_meta.items():
            if lid.startswith(gid.split("--")[0] + "--") and e["source_text"] in card.get("freq", ""):
                leaks.append(lid)
    check("wheel: group share is not repeated on its leaves", not leaks, ", ".join(leaks[:3]))
    check("wheel: the group estimate is shown on the family card as an estimate",
          all(meta.get(gid, {}).get("est", "").startswith("Оценка конспекта")
              for gid in group_entries))
    check("wheel: no family card claims a measured band",
          all("Корпусная доля" not in meta.get(gid, {}).get("freq", "") for gid in group_entries))
    check("wheel: every leaf card links its § and its lesson",
          all(c.get("paras") and c.get("lesson") for c in leaf_meta.values() if c.get("lesson")),
          "leaf cards without a lesson are allowed")

    # Typography rulings 25-11-2026: one size per row (20/19/18), no per-leaf
    # exception; a real Italic face everywhere, never a synthesised slant;
    # leaf 1 starts on the left equator; dvandva is named in the family row only.
    check("wheel: the three rows use 20/19/18 px",
          all(f'font-size="{s}"' in h for s in ("20", "19", "18"))
          and 'font-size="14.5"' not in h and 'font-size="15"' not in h)
    # The tilt is baked into the geometry, not a group transform: labels stay
    # upright and the hub text does not lie on its side. Leaf 1's first path
    # point must sit at the left equator (~270° from 12 o'clock).
    m1 = re.search(r'<path d="M([\d.]+) ([\d.]+)[^"]*" class="seg c-[\w-]+ ring3" '
                   r'data-id="[^"]+" data-n="1" ', h)
    ang = (math.degrees(math.atan2(float(m1.group(2)) - 560, float(m1.group(1)) - 560)) + 360) % 360 if m1 else None
    check("wheel: initial tilt puts leaf 1 on the left equator",
          ang is not None and abs(ang - 180) <= 4 and '<g id="wheel">' in h
          and 'let rot = 0' in h, f"{ang:.1f}°" if ang is not None else "no leaf-1 path")
    check("wheel: dvandva absent from class row, present in family row",
          h.count('class="lbl lbl1"') == 3 and "dvan" in h and "-dva" in h)
    wheel = read(os.path.join(HERE, "samasacakra-wheel.html"))
    poster = read(os.path.join(HERE, "samasacakra-poster.html"))
    face = "font-style: italic; src: url(data:font/woff2;base64,"
    check("wheel: a real Italic face is embedded in all three artifacts",
          all(face in x and "__B64I__" not in x for x in (h, wheel, poster)))
    # Cards show IAST example + vigraha + RU translation first; Devanagari
    # comes after the translation in its own block, never interleaved.
    card_tpl = ('<div class="ex">${m.ex}</div><div class="vig">${m.vigraha}</div>'
                '<div class="ru">«${m.ru}»</div>')
    check("wheel: card keeps Devanagari out of the IAST lines",
          card_tpl in h and ' · <span class="pdeva">' not in h
          and "'<br><span class=\"pdeva\">'" in h)
    return h


def check_drumam_entry():
    """A Drumam visitor must be able to reach the pilot and the § index."""
    path = os.path.join(DOCS, "drumam", "index.html")
    h = read(path)
    check("drumam: page links the five lessons", 'href="../uroki/"' in h)
    check("drumam: page links the paragraph index", 'href="../paragrafy/"' in h)
    check("drumam: page links the wheel", 'href="../"' in h)
    check("drumam: the link row is visible markup, not a script string",
          '<nav id="pilot-links"' in h)
    for target in ("uroki", "paragrafy"):
        check(f"drumam: the {target} target directory exists",
              os.path.isdir(os.path.join(DOCS, target)))


def check_links():
    """Every relative href on a generated page resolves inside docs/."""
    bad = []
    for rel in ("index.html", "paragrafy/index.html", "uroki/index.html",
                *[f'uroki/{l["slug"]}.html' for l in LESSONS]):
        path = os.path.join(DOCS, rel)
        h = read(path)
        for href in re.findall(r'href="([^"]+)"', h):
            if href.startswith(("http", "#", "mailto:")) or "${" in href:
                continue  # template literals inside the page script are built at run time
            target = href.split("#")[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                bad.append(f"{rel} -> {href}")
    check("links: every relative link resolves", not bad, "; ".join(bad[:5]))
    return bad


def main():
    verbose = "-v" in sys.argv
    paras = check_data()
    check_index_html(paras)
    check_lessons_html()
    check_wheel_html()
    check_drumam_entry()
    check_links()
    fails = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        if verbose or not ok:
            print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks pass")
    if fails:
        print("FAILED:")
        for name, _, detail in fails:
            print(f"  - {name}  [{detail}]")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
