#!/usr/bin/env python3
"""check_route_pilot.py — validator + deterministic generator for the H8620 bounded route pilot.

Single JSON source: docs/route/h8620_route_data.json
Static page:        docs/route/index.html  (regenerated from the JSON, never hand-edited)

Run:
    python scripts/check_route_pilot.py           # semantic checks + regen parity, exit 0/1
    python scripts/check_route_pilot.py --emit    # rewrite docs/route/index.html from the JSON

Checks (fail-closed, offline, no config/token reads):
  schema   — provenance set, formal cues carry condition/position/scope/strength/
             counterexample/change_of_conclusion + version, exactly three examples
             (simple / nested / underdetermined), candidate sets resolve to wheel ids;
  CLASS    — check_classification(): every example has candidates + a reasoned verdict;
             an underdetermined example keeps answer=[] and >=2 defended candidates;
  VIGRAHA  — check_vigraha(): a SEPARATE pass — status vocabulary, checked-in text
             matches the teaching-pack manifest, open examples carry >=2 defended
             formulations, source-only examples point at their source;
  links    — wheel leaf links (#k=<id>) resolve against docs/index.html META, lesson /
             diagram / published-URL targets exist or are declared external;
  honesty  — reconstruction labelled, coverage limits and the teacher-review gate
             before scored exercises are present in both JSON and page;
  surface  — the two checks render as separate revealable <details>, the page keeps
             status draft with NO script/automatic grading and carries no build
             metadata; the generated Pages start exposes exactly one route link;
  assets   — a relative (Pages) visual must live under docs/ AND be git-tracked;
             a repo-only file must use its GitHub blob URL instead.
  paths    — the published JSON and page carry no absolute local paths or private
             temp filenames; an access-controlled source renders as a plain
             reference, so the public page never requires a private link.

Existing generators are otherwise untouched: samasacakra wheel generation stays
deterministic (the Pages copy gains only its single navigation link).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "route" / "h8620_route_data.json"
PAGE = ROOT / "docs" / "route" / "index.html"
WHEEL = ROOT / "docs" / "index.html"
PACK = ROOT / "teaching-pack" / "example_pack_manifest.json"

CUE_FIELDS = ("condition", "position", "scope", "strength", "counterexample", "change_of_conclusion")
KINDS = ("simple", "nested", "underdetermined")
CLASS_STATUS = {"draft", "open"}
VIGRAHA_STATUS = {"source-only", "checked-in", "open"}

FAILURES: list[str] = []
RESULTS: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")
    RESULTS.append(msg)


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def wheel_ids() -> set[str]:
    html = WHEEL.read_text(encoding="utf-8")
    m = re.search(r"const META = (\{.*?\});\nconst GAL", html, re.S)
    if not m:
        raise SystemExit("FAIL  docs/index.html: META block not found (wheel page unreadable)")
    return set(json.loads(m.group(1)))


def wheel_names() -> dict[str, str]:
    """Human-readable card names: the route page shows names, not internal slugs."""
    html = WHEEL.read_text(encoding="utf-8")
    m = re.search(r"const META = (\{.*?\});\nconst GAL", html, re.S)
    return {k: v.get("name", k) for k, v in json.loads(m.group(1)).items()}


def pack_vigraha(manifest: dict) -> dict[str, str]:
    return {e["id"]: e["analytical_expansion"] for e in manifest["examples"]}


# ------------------------------------------------------------------ schema
def check_schema(d: dict, ids: set[str]) -> None:
    for key in ("route_id", "version", "handoff", "coverage", "sources", "cues", "candidates", "examples"):
        if not d.get(key):
            fail(f"schema: missing top-level `{key}`")
    cov = d.get("coverage", {})
    if cov.get("examples") != 3 or cov.get("new_attestations") != 0:
        fail("coverage: must declare exactly 3 examples and 0 new attestations")
    if len(cov.get("limits", [])) < 3:
        fail("coverage: fewer than three coverage limits recorded")
    if not cov.get("teacher_review_note") or "оцениваемых упражнений" not in cov["teacher_review_note"]:
        fail("coverage: teacher-review gate before scored exercises is not stated")
    if d.get("teacher_review_required") is not True:
        fail("teacher_review_required must be true")

    for sid, s in d["sources"].items():
        for f in ("label", "kind", "locator"):
            if not s.get(f):
                fail(f"source {sid}: missing `{f}`")
        if s.get("access") == "access-controlled":
            # a restricted source may carry no public address at all: its whole point
            # is that the page does not need one (availability / access note instead)
            if not (s.get("url") or s.get("path") or s.get("availability")
                    or s.get("access_note")):
                fail(f"source {sid}: access-controlled source needs a url, a path, "
                     f"a stated availability or an access note")
        elif "url" not in s and "path" not in s:
            fail(f"source {sid}: needs a url or a path")
        if s.get("url") and not str(s["url"]).startswith("https://"):
            fail(f"source {sid}: url must be https")

    for cue in d["cues"]:
        for f in CUE_FIELDS + ("id", "name", "version"):
            if not cue.get(f):
                fail(f"cue {cue.get('id', '?')}: missing `{f}`")
    if len({c["id"] for c in d["cues"]}) != len(d["cues"]):
        fail("cues: ids not unique")

    for cand in d["candidates"]:
        if len(cand.get("options", [])) < 1:
            fail(f"candidate {cand.get('id')}: no options")
        bad = [o for o in cand.get("options", []) if o not in ids]
        if bad:
            fail(f"candidate {cand.get('id')}: options not in wheel META: {bad}")
        if cand.get("open") and len(cand["options"]) < 2:
            fail(f"candidate {cand.get('id')}: open set must keep >=2 options")

    ex = d["examples"]
    if len(ex) != 3:
        fail(f"schema: expected 3 examples, got {len(ex)}")
    kinds = [e.get("kind") for e in ex]
    if sorted(kinds) != sorted(KINDS):
        fail(f"schema: kinds must be exactly one of {KINDS}, got {kinds}")
    cue_ids = {c["id"] for c in d["cues"]}
    cand_ids = {c["id"] for c in d["candidates"]}
    for e in ex:
        for f in ("id", "form", "label", "source", "observation", "candidate_set",
                  "cue_refs", "wheel_leaf_link", "wheel_leaf_id", "visual",
                  "classification", "vigraha", "reconstruction"):
            if f not in e:
                fail(f"example {e.get('id', '?')}: missing `{f}`")
        if e.get("source") not in d["sources"]:
            fail(f"example {e.get('id')}: source `{e.get('source')}` not in provenance set")
        if e.get("candidate_set") not in cand_ids:
            fail(f"example {e.get('id')}: unknown candidate set `{e.get('candidate_set')}`")
        for r in e.get("cue_refs", []):
            if r not in cue_ids:
                fail(f"example {e.get('id')}: unknown cue `{r}`")
    recs = [e for e in ex if e.get("reconstruction")]
    if not (len(recs) == 1 and recs[0]["kind"] == "underdetermined" and "еконструкц" in recs[0]["label"]):
        fail("exactly the underdetermined example may be a labelled reconstruction")
    if any("еконструкц" in e["label"] for e in ex if not e.get("reconstruction")):
        fail("non-reconstruction example is labelled as a reconstruction")
    ok("schema: provenance, cues, candidate sets and 3 example kinds are complete")


# ------------------------------------------------------------------ 1) classification + reason (separate pass)
def check_classification(d: dict, ids: set[str]) -> None:
    seen = 0
    for e in d["examples"]:
        cl = e.get("classification") or {}
        st = cl.get("status")
        ans = cl.get("answer")
        reason = str(cl.get("reason", "")).strip()
        cand = next(c for c in d["candidates"] if c["id"] == e["candidate_set"])
        if st not in CLASS_STATUS:
            fail(f"class/{e['id']}: bad status {st!r} (want {sorted(CLASS_STATUS)})")
            continue
        if len(reason) < 60:
            fail(f"class/{e['id']}: reason too short to be a reason")
        if not isinstance(ans, list):
            fail(f"class/{e['id']}: answer must be a list")
        elif ans:
            if st == "open":
                fail(f"class/{e['id']}: an open example must keep answer=[]")
            bad = [a for a in ans if a not in ids]
            if bad:
                fail(f"class/{e['id']}: verdict ids not in wheel META: {bad}")
        else:  # empty verdict: only legal for an open candidate set
            if st != "open":
                fail(f"class/{e['id']}: empty verdict but status is {st!r}")
            if not cand.get("open"):
                fail(f"class/{e['id']}: empty verdict but candidate set is not open")
            if len(cand["options"]) < 2:
                fail(f"class/{e['id']}: open verdict needs >=2 defended candidates")
        if st == "open" and not cand.get("open"):
            fail(f"class/{e['id']}: open status over a closed candidate set")
        elif st != "open" and cand.get("open"):
            fail(f"class/{e['id']}: closed verdict over an open candidate set")
        if ans and not set(ans) <= set(cand["options"]):
            fail(f"class/{e['id']}: verdict outside its candidate set")
        seen += 1
    ok(f"classification: {seen}/3 examples carry a candidate-restricted verdict + reason "
       f"(separate pass, status draft|open)")


# ------------------------------------------------------------------ 2) vigraha (separate pass)
def check_vigraha(d: dict, manifest: dict) -> None:
    pack = pack_vigraha(manifest)
    seen = 0
    for e in d["examples"]:
        v = e.get("vigraha") or {}
        st = v.get("status")
        if st not in VIGRAHA_STATUS:
            fail(f"vigraha/{e['id']}: bad status {st!r} (want {sorted(VIGRAHA_STATUS)})")
            continue
        if not v.get("allowed"):
            fail(f"vigraha/{e['id']}: no allowed-answer list")
        if not str(v.get("reason", "")).strip():
            fail(f"vigraha/{e['id']}: no reason for the status")
        if st == "checked-in":
            if not v.get("text"):
                fail(f"vigraha/{e['id']}: checked-in status without the vigraha text")
            elif not any(v["text"] in exp for exp in pack.values()):
                fail(f"vigraha/{e['id']}: text not attested in the teaching-pack manifest")
        if st == "open" and len(v.get("allowed") or []) < 2:
            fail(f"vigraha/{e['id']}: open status needs >=2 defended formulations")
        if st == "source-only" and not v.get("allowed"):
            fail(f"vigraha/{e['id']}: source-only status needs a source pointer")
        seen += 1
    ok(f"vigraha: {seen}/3 examples pass the separate vigraha check "
       f"(source-only | checked-in vs manifest | open with >=2 formulations)")


# ------------------------------------------------------------------ links + honesty
def check_links(d: dict, ids: set[str], root: Path) -> None:
    for e in d["examples"]:
        for key in ("wheel_leaf_link", "second_wheel_leaf_link"):
            link = e.get(key)
            if not link:
                continue
            m = re.fullmatch(r"\.\./index\.html#k=([\w-]+)", link)
            if not m:
                fail(f"link/{e['id']}:{key}: wheel link must be ../index.html#k=<id>, got {link}")
            elif m.group(1) not in ids:
                fail(f"link/{e['id']}:{key}: {m.group(1)} not in wheel META")
        if not str(e.get("wheel_link_note", "")).strip():
            fail(f"link/{e['id']}: wheel link carries no note")
        vis = e.get("visual") or {}
        if vis.get("kind") not in ("source-render", "published-diagram"):
            fail(f"link/{e['id']}: visual must be a source render or a published diagram")
        path = vis.get("path")
        if path and not (root / path).is_file():
            fail(f"link/{e['id']}: visual path {path} not on disk")
        if vis.get("kind") == "published-diagram" and not vis.get("url"):
            fail(f"link/{e['id']}: published diagram has no url")
        lesson = e.get("lesson_link")
        if lesson and not (root / "docs" / lesson.lstrip("./")).is_file():
            fail(f"link/{e['id']}: lesson link {lesson} not on disk")
    # provenance paths that claim to be in git must exist
    for sid, s in d["sources"].items():
        if s.get("in_git") and s.get("path") and not (root / s["path"]).is_file():
            fail(f"provenance/{sid}: in_git path {s['path']} not on disk")
    ok("links: wheel leaf links resolve to docs/index.html META, visuals and lesson targets exist")


def check_honesty(d: dict) -> None:
    blob = json.dumps(d, ensure_ascii=False)
    for token in ("W16-3701", "H8618", "data-qmode",
                  "teacher_review", "Реконструкция", "na putraḥ", "avidyamānaḥ putraḥ",
                  "слайд 19", "compounds_pptx"):
        if token not in blob:
            fail(f"honesty: `{token}` not carried in the JSON source")
    # coverage claims corrected on 26-11-2026 must not come back: the single Google Doc
    # IS the complete Yoga-Vasishtha archive, and the LiveJournal posts are separate
    # authored publications rather than a second archive behind an access blocker
    for gone in ("обоих архивов", "охват архива ЖЖ не установлен"):
        if gone in blob:
            fail(f"honesty: corrected coverage claim `{gone}` is back in the JSON source")
    ex = {e["id"]: e for e in d["examples"]}
    nan = ex.get("nan-reconstruction", {})
    if nan.get("segmentation") != "shared":
        fail("honesty: the underdetermined example must declare segmentation=shared")
    if nan.get("form") != "aputraḥ":
        fail(f"honesty: form must be aputraḥ, got {nan.get('form')!r}")
    if nan.get("source") != "compounds_pptx":
        fail("honesty: aputraḥ must cite compounds.pptx (slide 19) as its source")
    reason = (nan.get("classification", {}).get("reason") or "") + \
             " " + (nan.get("vigraha", {}).get("reason") or "")
    # a claim of DIFFERENT segmentation is forbidden; the explicit disclaimer is fine
    bad_seg = [m for m in re.finditer(r"различ\w*\s+членени|разное членение|разными членениями",
                                      reason, re.I)
               if not re.search(r"не утвержд|общее|только", reason[max(0, m.start() - 60):m.end() + 60])]
    if bad_seg:
        fail("honesty: an analysis must not claim DIFFERENT segmentation for aputraḥ")
    if "членени" not in reason:
        fail("honesty: aputraḥ reason must state what happens to segmentation")
    nested = ex.get("sitosna-nested", {})
    if "внутренн" not in nested.get("observation", "").lower() or \
            "внешн" not in nested.get("observation", "").lower():
        fail("honesty: nested example must distinguish inner dvandva from the outer node")
    if not str(nested.get("manifest_ref", "")).startswith("teaching-pack/example_pack_manifest.json"):
        fail("honesty: nested example must cite the teaching-pack manifest entry")
    if not str(nested.get("config_ref", "")).endswith("klammerdiagramm-sitosnasukhaduhkhadah.json"):
        fail("honesty: nested example must cite its actual render config")
    for e in d["examples"]:
        if "adīta" in json.dumps(e, ensure_ascii=False):
            fail(f"honesty: example {e['id']} carries the typo adīta (want adhīta)")
    ok("honesty: slide-19 evidence, shared segmentation, inner/outer split and "
       "adhīta spelling are carried in the data")


def check_surface(page_text: str) -> None:
    """Page-level honesty: revealable separate checks, draft, no grading, no build filler."""
    if page_text.count("<details") < 2:
        fail("surface: the two checks must render as >=2 revealable <details> blocks")
    if "<script" in page_text.lower():
        fail("surface: route page must carry no script (no automatic grading)")
    for filler in ("check_route_pilot", "Генератор колеса", "--emit", "Сборка:"):
        if filler in page_text:
            fail(f"surface: build metadata/filler `{filler}` leaked into the page")
    if "draft" not in page_text or "оцениваемых упражнений" not in page_text:
        fail("surface: draft status / scored-exercise gate missing from the page")
    if "статус open" not in page_text and "статус draft" not in page_text:
        fail("surface: per-check status is not shown")
    ok("surface: checks are separate <details>, status draft, no script, no build filler")


# local paths / private temp filenames are never publishable (H8620 editorial correction)
LOCAL_MARKERS = ("C:/", "C:\\", "AppData", "/Temp/", "\\Temp\\", "Users/COMPUTER",
                 "LEITAN_PUBLIC_SOURCE_AUDIT", "h8604-source-audit", "h8603-audit-2611",
                 "compounds.pptx")


def check_published_paths(d: dict, html: str) -> None:
    """Neither the JSON source nor the generated page may carry absolute local paths
    or private temp filenames; restricted evidence is cited by an access-controlled
    reference instead."""
    for name, text in (("h8620_route_data.json", json.dumps(d, ensure_ascii=False)),
                       ("index.html", html)):
        hits = sorted(m for m in LOCAL_MARKERS if m in text)
        if hits:
            fail(f"paths: {name} carries local path / private filename material: {hits}")
    ok("paths: no absolute local paths or private temp filenames in the published JSON/HTML")


def check_pages_nav(root: Path) -> None:
    """The Pages start exposes the route through exactly one generated link."""
    idx = root / "docs" / "index.html"
    html = idx.read_text(encoding="utf-8")
    n = html.count('href="route/"')
    if n != 1:
        fail(f"pages-nav: docs/index.html must carry exactly one route link, found {n}")
    else:
        ok("pages-nav: exactly one generated navigation link to route/ on the Pages start")


def check_visual_deploy(d: dict, root: Path) -> None:
    """A relative visual URL must actually deploy with Pages (git-tracked under docs/);
    a repo-only file must use its GitHub blob URL; a public source render may be its own URL."""
    import subprocess
    for e in d["examples"]:
        vis = e.get("visual") or {}
        url, path, kind = str(vis.get("url", "")), str(vis.get("path", "")), vis.get("kind")
        if kind == "source-render":
            if not url.startswith("https://"):
                fail(f"deploy/{e['id']}: source render must be an https public URL, got {url}")
            continue
        if url.startswith(".."):  # Pages-relative: must resolve inside docs/ and be tracked
            target = (root / "docs" / "route" / url).resolve()
            if root / "docs" not in target.parents:
                fail(f"deploy/{e['id']}: relative visual {url} escapes docs/")
                continue
            if not target.is_file():
                fail(f"deploy/{e['id']}: relative visual {url} not on disk")
            r = subprocess.run(["git", "ls-files", "--error-unmatch",
                                str(target.relative_to(root))],
                               cwd=str(root), capture_output=True)
            if r.returncode != 0:
                fail(f"deploy/{e['id']}: {url} is not git-tracked → it will NOT deploy on Pages; "
                     f"use the GitHub blob URL for a repo-only file")
        elif "github.com/gasyoun/SamasaChakram/blob/" not in url:
            fail(f"deploy/{e['id']}: repo-only diagram must use its GitHub blob URL, got {url}")
        elif path and not (root / path).is_file():
            fail(f"deploy/{e['id']}: blob target path {path} not on disk")
    ok("deploy: every visual URL is Pages-reachable (relative + tracked), a blob URL, "
       "or a public source render")


# ------------------------------------------------------------------ deterministic generator
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def addr(sv: dict, link_text: str | None = None) -> str:
    """Address fragment for one source.

    A public https URL becomes an anchor (`link_text` or the URL itself). An
    access-controlled source stays a PLAIN reference — the public page carries no
    private link and needs none to be read. Otherwise the checked-in path or the
    declared availability is shown. Empty string when the source declares nothing.
    """
    if sv.get("access") == "access-controlled":
        out = ""
        ref = sv.get("url") or sv.get("path")
        if ref:
            out += f"<code>{esc(str(ref))}</code> "
        if sv.get("availability"):
            out += f'<span class="mut">{esc(sv["availability"])}</span> '
        note = sv.get("access_note") or "материал с ограниченным доступом — для чтения страницы не требуется"
        return out + f'<span class="mut">({esc(note)})</span>'
    if sv.get("url"):
        return f'<a href="{sv["url"]}">{esc(link_text or sv["url"])}</a>'
    if sv.get("path"):
        return f"<code>{esc(sv['path'])}</code>"
    if sv.get("availability"):
        return f'<span class="mut">{esc(sv["availability"])}</span>'
    return ""


def diagram(vis: dict, root: Path) -> str:
    "Inline the canonical checked-in SVG so the diagram is visible on Pages."
    path = str(vis.get("path") or "")
    if not path.endswith(".svg") or not (root / path).is_file():
        return ""
    svg = (root / path).read_text(encoding="utf-8").strip()
    cap = esc(vis.get("caption") or vis.get("label"))
    return (f'<figure class="diagram" role="group" aria-label="{cap}">'
            + svg + f'<figcaption>{cap}</figcaption></figure>')


def render(d: dict) -> str:
    s = d["sources"]
    names = wheel_names()
    out: list[str] = []
    a = out.append
    a("<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n<meta charset=\"utf-8\">")
    a('<meta name="viewport" content="width=device-width, initial-scale=1">')
    a(f"<title>{esc(d['title'])} · H8620</title>")
    a("<style>\n:root{--ink:#1b1a17;--mut:#6b6558;--line:#e2ddd2;--bg:#faf7f0;--warn:#8a2f1d}\n"
      "body{font:16px/1.55 Georgia,'Times New Roman',serif;color:var(--ink);background:var(--bg);"
      "margin:0 auto;max-width:52rem;padding:1.5rem 1rem}\nh1{font-size:1.5rem;margin:.2rem 0}"
      "h2{font-size:1.15rem;border-bottom:1px solid var(--line);padding-bottom:.3rem;margin-top:2rem}"
      ".banner{border:2px solid var(--warn);color:var(--warn);padding:.6rem .8rem;border-radius:4px;"
      "font-weight:bold;background:#fff}\n.banner small{display:block;font-weight:normal;color:var(--ink)}"
      ".ex{border:1px solid var(--line);background:#fff;border-radius:6px;padding:.8rem 1rem;margin:1rem 0}"
      ".form{font-size:1.25rem;font-style:italic}\n.kind{font-size:.8rem;letter-spacing:.06em;"
      "text-transform:uppercase;color:var(--mut)}\n.recon{color:var(--warn);font-weight:bold}"
      ".row{display:grid;grid-template-columns:11rem 1fr;gap:.2rem .8rem;margin:.5rem 0}"
      ".row b{font-weight:normal;color:var(--mut);font-size:.85rem;text-transform:uppercase;"
      "letter-spacing:.04em}\n.cue{background:#fff;border:1px solid var(--line);border-radius:6px;"
      "padding:.6rem .9rem;margin:.6rem 0}\n.cue h3{margin:.1rem 0 .4rem;font-size:1rem}"
      "table{border-collapse:collapse;width:100%;background:#fff;font-size:.95rem}"
      "td,th{border:1px solid var(--line);padding:.35rem .5rem;text-align:left;vertical-align:top}"
      "a{color:#1a4a7a}\n.mut{color:var(--mut)}\ncode{font-size:.95em;overflow-wrap:anywhere}\n"
      ".ans{background:#f2f6ee;"
      "border-left:3px solid #4a7a3a;padding:.35rem .6rem;margin:.3rem 0}\n.open{background:#fdf3ef;"
      "border-left:3px solid var(--warn);padding:.35rem .6rem;margin:.3rem 0}\n"
      ".row{display:grid;grid-template-columns:minmax(0,11rem) minmax(0,1fr);gap:.2rem .8rem;margin:.5rem 0}\n"
      ".row>*{min-width:0;overflow-wrap:anywhere}\n"
      ".ex,.cue{overflow-wrap:anywhere}\n"
      "table{border-collapse:collapse;width:100%;background:#fff;font-size:.95rem;table-layout:fixed}\n"
      "td,th{border:1px solid var(--line);padding:.35rem .5rem;text-align:left;vertical-align:top;"
      "overflow-wrap:anywhere;word-break:break-word}\n"
      "@media (max-width:480px){.row{grid-template-columns:1fr;gap:0}"
      "body{padding:1rem .75rem}.form{font-size:1.1rem}}\n"
      "details.check{margin:.4rem 0;border:1px solid var(--line);border-radius:4px;background:#fff}\n"
      "details.check>summary{cursor:pointer;padding:.4rem .6rem;font-weight:bold;"
      "font-size:.9rem;letter-spacing:.03em}\n"
      "details.check[open]>summary{border-bottom:1px solid var(--line)}\n"
      "details.check .ans,details.check .open{border:0;border-radius:0}\n"
      ".diagram{margin:.8rem 0;background:#fff;border:1px solid var(--line);border-radius:6px;padding:.6rem}\n"
      ".diagram svg{display:block;max-width:100%;height:auto;margin:0 auto}\n"
      ".diagram figcaption{font-size:.85rem;color:var(--mut);margin-top:.4rem}\n</style>\n</head>\n<body>")
    a(f"<h1>{esc(d['title'])}</h1>")
    a(f'<p class="mut">Статический маршрут пилота H8620 · версия {esc(d["version"])} · '
      f'данные: <a href="h8620_route_data.json"><code>h8620_route_data.json</code></a> · '
      f'{esc(d["created"])}</p>')
    a('<div class="banner">Пилот в статусе draft: ни один пример не допущен до оцениваемых упражнений без проверки преподавателем.'
      f'<small>{esc(d["coverage"]["teacher_review_note"])}</small></div>')
    tb = s.get("teacher_brief") or {}
    if tb.get("url"):
        a(f'<p class="mut">Преподавателю: <a href="{tb["url"]}">{esc(tb["label"])}</a></p>')
    va = s.get("visual_annotation") or {}
    if va.get("url"):
        a(f'<p class="mut">Упражнение на чтение по блоку 66.1: '
          f'<a href="{va["url"]}">{esc(va["label"])}</a></p>')
    a("<h2>Покрытие и ограничения</h2><ul>")
    for lim in d["coverage"]["limits"]:
        a(f"<li>{esc(lim)}</li>")
    a("</ul>")
    a('<p class="mut">Пройти маршрут: откройте лепесток колеса по ссылке примера, затем '
      'сверьте признак и отдельную проверку vigraha.</p>')

    a("<h2>Примеры маршрута</h2>")
    for e in d["examples"]:
        a('<div class="ex">')
        a(f'<div class="kind">{esc(e["kind"])}'
          + (' · <span class="recon">реконструкция — не аттестация</span>' if e.get("reconstruction") else "")
          + "</div>")
        a(f'<div class="form">{esc(e["form"])}</div>')
        a(f'<p>{esc(e["label"])} — {esc(e["observation"])}</p>')
        if e.get("node_labels"):
            a('<div class="row"><b>Узлы</b><span>' +
              "; ".join(f"<b>{esc(k)}</b>: {esc(v)}" for k, v in e["node_labels"].items()) +
              "</span></div>")
        if e.get("source_anchor"):
            a(f'<div class="row"><b>Стих</b><span><i>{esc(e["source_anchor"])}</i></span></div>')
        if e.get("referent_hint"):
            a(f'<div class="row"><b>Референт</b><span>{esc(e["referent_hint"])}</span></div>')
        src = s[e["source"]]
        corr = s.get(e.get("corroborating_source", ""), {})
        src_addr, corr_addr = addr(src, "открыть"), addr(corr, "открыть")
        a('<div class="row"><b>Источник</b><span>' + esc(src["label"]) +
          (f" — {src_addr}" if src_addr else "") + "</span></div>")
        if corr:
            a('<div class="row"><b>Сверка</b><span>' + esc(corr["label"]) +
              (f" — {corr_addr}" if corr_addr else "") + "</span></div>")
        a(f'<div class="row"><b>Лепесток колеса</b><span><a href="{e["wheel_leaf_link"]}">'
          f'{esc(e.get("wheel_link_label") or names.get(e["wheel_leaf_id"], e["wheel_leaf_id"]))}</a>')
        if e.get("second_wheel_leaf_link"):
            a(f' · <a href="{e["second_wheel_leaf_link"]}">'
              f'{esc(e.get("second_wheel_link_label") or names.get(e["second_wheel_leaf_id"], e["second_wheel_leaf_id"]))}</a>')
        a(f' <span class="mut">— {esc(e["wheel_link_note"])}</span></span></div>')
        if e.get("lesson_link"):
            a(f'<div class="row"><b>Урок</b><span><a href="{e["lesson_link"]}">урок 2: '
              "вложенная двандва</a>"
              + (f' <span class="mut">— {esc(e["lesson_note"])}</span>' if e.get("lesson_note") else "")
              + "</span></div>")
        vis = e["visual"]
        a(f'<div class="row"><b>Визуальный источник</b><span><a href="{vis["url"]}">{esc(vis["label"])}</a>'
          + (f' <span class="mut">— {esc(vis["note"])}</span>' if vis.get("note") else "") + "</span></div>")
        fig = diagram(vis, ROOT)
        if fig:
            a(fig)
        if e.get("manifest_ref"):
            a(f'<div class="row"><b>Манифест</b><span><code>{esc(e["manifest_ref"])}</code></span></div>')
        if e.get("config_ref"):
            a(f'<div class="row"><b>Конфиг схемы</b><span><code>{esc(e["config_ref"])}</code></span></div>')
        if e.get("scheme_status"):
            a(f'<div class="row"><b>Схема и рубрика</b><span>Схема: {esc(e["scheme_status"])} · '
              f'Рубрика: {esc(e["classification"]["status"])}</span></div>')
        if e.get("alternate_grouping"):
            ag = e["alternate_grouping"]
            a(f'<div class="row"><b>Альтернатива</b><span><span class="mut">статус {esc(ag["status"])}</span> — '
              f'{esc(ag["text"])}</span></div>')
        if e.get("segmentation") == "shared":
            a('<div class="row"><b>Членение</b><span>общее для обеих трактовок (a- + putraḥ): '
              "контраст — семантическое отношение и референт, не границы членов</span></div>")
        if e.get("contrast_contexts"):
            items = "".join(
                f'<li><b>{esc(c.get("analysis_label") or names.get(c["analysis"], c["analysis"]))}</b> '
                f'<span class="mut">({esc(c["status"])})</span><br>{esc(c["context"])}<br>'
                f'{esc(c["reading"])}</li>'
                for c in e["contrast_contexts"])
            a(f'<div class="row"><b>Контексты</b><span><ul>{items}</ul></span></div>')
        if e.get("source_check"):
            a(f'<div class="row"><b>Сверка источника</b><span>{esc(e["source_check"])}</span></div>')
        if e.get("isolation_note"):
            a(f'<div class="row"><b>Изолированно</b><span>{esc(e["isolation_note"])}</span></div>')
        cand = next(c for c in d["candidates"] if c["id"] == e["candidate_set"])
        a(f'<div class="row"><b>Кандидаты</b><span>{esc(cand["question"])} · '
          + ", ".join(f"{esc(names.get(o, o))}" for o in cand["options"]) + "</span></div>")
        cues = [c for c in d["cues"] if c["id"] in e["cue_refs"]]
        a('<div class="row"><b>Признаки</b><span>' +
          ", ".join(f'<a href="#{c["id"]}">{esc(c["name"])}</a>' for c in cues) + "</span></div>")
        cl = e["classification"]
        box = "open" if cl["status"] == "open" else "ans"
        verdict = ", ".join(f"{esc(names.get(v, v))}" for v in cl["answer"]) or "<i>выбор открыт</i>"
        a(f'<details class="check"><summary>Самопроверка 1 — класс и довод · статус {esc(cl["status"])}</summary>'
          f'<div class="{box}">Класс: {verdict}<br>Довод: {esc(cl["reason"])}<br>'
          f'Правило решения (после ответа): {esc(cand["decision_rule"])}</div></details>')
        v = e["vigraha"]
        vextra = ""
        if v["status"] == "checked-in" and v.get("text"):
            vextra = "Vigraha: <i>" + esc(v["text"]) + "</i><br>"
        elif v["status"] == "open":
            vextra = ("Защищаемые трактовки:<ul>" +
                      "".join(f"<li>{esc(x)}</li>" for x in v["allowed"]) + "</ul>")
        elif v["status"] == "source-only":
            vextra = esc(v["allowed"][0]) + "<br>"
        a(f'<details class="check"><summary>Самопроверка 2 — vigraha · статус {esc(v["status"])}</summary>'
          f'<div class="{"open" if v["status"] == "open" else "ans"}">{vextra}'
          f'Основание: {esc(v["reason"])}</div></details>')
        a("</div>")

    a("<h2>Формальные признаки</h2>")
    for c in d["cues"]:
        a(f'<div class="cue" id="{c["id"]}"><h3>{esc(c["name"])} <span class="mut">({esc(c["version"])})</span></h3>')
        a('<div class="row">')
        for f in CUE_FIELDS:
            title = {"condition": "Условие", "position": "Позиция", "scope": "Область",
                     "strength": "Сила вывода", "counterexample": "Контрпример",
                     "change_of_conclusion": "Что меняет вывод"}[f]
            a(f'<b>{title}</b><span>{esc(c[f])}</span>')
        a("</div></div>")

    a("<h2>Источники (провенанс)</h2><table><tr><th>id</th><th>метка</th><th>тип</th><th>адрес</th></tr>")
    for sid, sv in s.items():
        link = addr(sv) or '<span class="mut">—</span>'
        a(f"<tr><td><code>{esc(sid)}</code></td><td>{esc(sv['label'])}</td>"
          f"<td>{esc(sv['kind'])}</td><td>{link}</td></tr>")
    a("</table>")
    a("</body>\n</html>\n")
    return "\n".join(out)


def main() -> int:
    emit = "--emit" in sys.argv[1:]
    d = load()
    ids = wheel_ids()
    check_schema(d, ids)
    check_classification(d, ids)
    check_vigraha(d, json.loads(PACK.read_text(encoding="utf-8")))
    check_links(d, ids, ROOT)
    check_honesty(d)
    check_visual_deploy(d, ROOT)
    check_pages_nav(ROOT)
    html = render(d)
    check_published_paths(d, html)
    if emit:
        PAGE.parent.mkdir(parents=True, exist_ok=True)
        PAGE.write_text(html, encoding="utf-8", newline="\n")
        print(f"emit  {PAGE.relative_to(ROOT)} regenerated from JSON ({len(html)} bytes)")
    else:
        if not PAGE.is_file():
            fail(f"parity: {PAGE.name} missing — run --emit")
        elif PAGE.read_text(encoding="utf-8") != html:
            fail("parity: docs/route/index.html differs from the JSON source — run --emit")
        else:
            ok("parity: page is byte-identical to the JSON source (deterministic generator)")
    check_surface(html)
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s)")
        return 1
    print("\nall route-pilot checks green")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
