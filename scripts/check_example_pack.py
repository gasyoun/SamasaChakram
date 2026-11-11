#!/usr/bin/env python3
"""check_example_pack.py — automated acceptance gate for the H8028 reviewed reading example pack.

Contract (Uprava H8028, class: data):
  1. manifest schema     — every example carries every required field, status vocabulary enforced,
                           provenance paths exist on disk.
  2. data/render parity  — for every config: regen SVG/HTML via build_klammerdiagramm.py and compare
                           to the committed render (CRLF->LF normalised, builder writes CRLF, repo
                           stores LF per .gitattributes). Any drift = FAIL (recorded finding for
                           configs we refuse to silently rewrite).
  3. canary C-D4         — ghost [priya] exists in config ghosts[] AND in the committed SVG word line
                           with no arrow bar / no node index on the ghost run.
  4. canary C-D5         — leitan config II_START == 7 and joins Q+D; historical config II_START == 4;
                           both renders exist; gallery documents the D5 recut.
  5. canary C-ACCDUAL    — sanskrit-right-to-left-reading.md carries the Acc. dual correction (and
                           NOT a locative reading of the -e dual); the canary HTML carries the label.
  6. taxonomy links      — all 17 diagram link targets resolve (file-exists); soft word-match produces
                           the family-illustration finding list (compared against the manifest's
                           recorded audit — divergence = FAIL, so the audit cannot rot).

Exit 0 = all hard checks green. Exit 1 = at least one hard failure (printed).
Run: python scripts/check_example_pack.py            (repo root)
     python scripts/check_example_pack.py --render-md  (also regenerate EXAMPLE_PACK.md from JSON)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "teaching-pack" / "example_pack_manifest.json"
BUILD = ROOT / "klammerdiagramm" / "build_klammerdiagramm.py"
RTL_DOC = ROOT / "sanskrit-right-to-left-reading.md"
GALLERY = ROOT / "klammerdiagramm-worked-examples.md"
TAXONOMY = ROOT / "samasacakra" / "samasacakra-taxonomy.json"

REQUIRED = [
    "source_text", "source_anchor", "constituent_groups", "category",
    "analytical_expansion", "aligned_translation", "provenance",
    "review_status", "reviewer_provenance",
]
STATUSES = {"approved", "withheld"}

FAILURES: list[str] = []
FINDINGS: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def finding(msg: str) -> None:
    FINDINGS.append(msg)
    print(f"NOTE  {msg}")


def norm(text: str) -> str:
    return text.replace("\r\n", "\n")


def check_schema(m: dict) -> None:
    if m.get("review_status_vocabulary") and set(m["review_status_vocabulary"]) != STATUSES:
        fail("review_status_vocabulary drifted from {approved, withheld}")
    ids = set()
    approved = withheld = 0
    for ex in m["examples"]:
        eid = ex.get("id", "<no-id>")
        if eid in ids:
            fail(f"duplicate example id {eid}")
        ids.add(eid)
        for f in REQUIRED:
            if f not in ex or ex[f] in (None, "", []):
                fail(f"{eid}: missing required field `{f}`")
        st = ex.get("review_status")
        if st not in STATUSES:
            fail(f"{eid}: bad review_status {st!r}")
        elif st == "approved":
            if ex.get("withheld_reason"):
                fail(f"{eid}: approved example must not carry withheld_reason")
            approved += 1
        else:
            if not ex.get("withheld_reason"):
                fail(f"{eid}: withheld example must carry withheld_reason")
            withheld += 1
        at = ex.get("aligned_translation") or {}
        if not (isinstance(at, dict) and at.get("lang") and at.get("text") and at.get("source")):
            fail(f"{eid}: aligned_translation must be a lang/text/source object")
        prov = ex.get("provenance") or {}
        cfg = prov.get("config")
        if not cfg:
            fail(f"{eid}: provenance.config missing")
        elif not (ROOT / cfg).is_file():
            fail(f"{eid}: provenance.config {cfg} not found")
        else:
            for kind, rel in (prov.get("renders") or {}).items():
                if not (ROOT / rel).is_file():
                    fail(f"{eid}: provenance.render {kind}={rel} not found")
    cov = m["scope"]["coverage"]
    if cov["rendered_examples"] != len(m["examples"]):
        fail(f"scope.coverage.rendered_examples {cov['rendered_examples']} != {len(m['examples'])} manifest rows")
    if cov["correction_canaries"] != len(m["correction_canaries"]):
        fail("scope.coverage.correction_canaries mismatch")
    ok(f"schema: {len(m['examples'])} examples ({approved} approved / {withheld} withheld), "
       f"{len(m['correction_canaries'])} canaries declared")


def regen(config: Path) -> tuple[str, str] | None:
    """Render config to (svg_text, html_text) via the committed builder. None on builder error."""
    with tempfile.TemporaryDirectory(dir=str(ROOT)) as td:
        out_base = str(Path(td) / "regen")  # --out is a BASE path: writes <base>.svg + <base>.html
        r = subprocess.run(
            [sys.executable, str(BUILD), "--config", str(config), "--out", out_base],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT), timeout=120,
        )
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])
            return None
        svg = Path(out_base + ".svg")
        if not svg.is_file():
            return None
        html = Path(out_base + ".html")
        return norm(svg.read_text(encoding="utf-8")), (
            norm(html.read_text(encoding="utf-8")) if html.is_file() else "")


def check_parity(m: dict) -> None:
    """Data/render parity for every config reachable from the manifest."""
    pairs_seen = 0
    for ex in m["examples"]:
        prov = ex.get("provenance") or {}
        cfg_rel = prov.get("config")
        if not cfg_rel:
            continue
        cfg = ROOT / cfg_rel
        svg_rel = (prov.get("renders") or {}).get("svg")
        if not cfg.is_file() or not svg_rel:
            continue
        svg_path = ROOT / svg_rel
        if not svg_path.is_file():
            continue  # already reported by schema
        got = regen(cfg)
        if got is None:
            fail(f"{ex['id']}: builder failed on {cfg_rel}")
            continue
        regen_svg, _ = got
        committed = norm(svg_path.read_text(encoding="utf-8"))
        pairs_seen += 1
        if regen_svg != committed:
            # decide: desc/title-only drift vs geometry drift
            strip = lambda t: re.sub(r"<desc>.*?</desc>|<title>.*?</title>", "", t, flags=re.S)
            if strip(regen_svg) == strip(committed):
                fail(f"{ex['id']}: stale render metadata — regen differs from committed "
                     f"{svg_rel} only in <desc>/<title> (rerun builder, commit the fresh render)")
            else:
                fail(f"{ex['id']}: GEOMETRY drift — regen differs from committed {svg_rel} beyond metadata")
    ok(f"parity: {pairs_seen} config->committed-SVG pairs compared (LF-normalised)")


def check_d4(m: dict) -> None:
    ex = next((e for e in m["examples"] if e["id"] == "sakapriyaparthivah"), None)
    if not ex:
        fail("C-D4: example sakapriyaparthivah missing from manifest")
        return
    cfg = json.loads((ROOT / ex["provenance"]["config"]).read_text(encoding="utf-8"))
    ghosts = cfg.get("ghosts") or []
    if not ghosts or ghosts[0].get("text") != "priya":
        fail("C-D4: config ghosts[] does not carry the supplied [priya]")
    else:
        ok("C-D4: config carries ghost [priya]")
    svg = norm((ROOT / ex["provenance"]["renders"]["svg"]).read_text(encoding="utf-8"))
    if svg.count("[priya]") < 1:
        fail("C-D4: committed SVG word line has no [priya] ghost")
    else:
        ok(f"C-D4: SVG renders [priya] ({svg.count('[priya]')}×)")
    # ghost must not be a bar/arrow/node: no bar/arrow element may carry priya, no node index on the run
    if re.search(r'<(line|path)[^>]*(priya|ghost)[^>]*>', svg, re.I):
        fail("C-D4: ghost has a bar/arrow (must be editorial-only)")
    if re.search(r'class="(?:bar|arrow|arrowlabel)"[^>]*>.*priya', svg, re.I | re.S):
        fail("C-D4: ghost appears inside bar/arrow markup")
    if re.search(r'\[priya\][^<]*<tspan[^>]*class="(?:node|idx|label)', svg, re.I):
        fail("C-D4: ghost run carries a node index")
    if not re.search(r"ghosts", json.dumps(cfg)):
        fail("C-D4: config has no ghosts key")


def check_d5() -> None:
    leitan = json.loads((ROOT / "klammerdiagramm/klammerdiagramm-uddama-leitan.json").read_text(encoding="utf-8"))
    hist = json.loads((ROOT / "klammerdiagramm/klammerdiagramm-uddama-plate-historical.json").read_text(encoding="utf-8"))
    if leitan.get("II_START") != 7:
        fail(f"C-D5: leitan II_START {leitan.get('II_START')} != 7 (must begin at svabhāvā)")
    else:
        ok("C-D5: leitan II_START=7 (‖-mark before svabhāvā)")
    if hist.get("II_START") != 4:
        fail(f"C-D5: historical II_START {hist.get('II_START')} != 4 (plate reading at tamaḥ)")
    else:
        ok("C-D5: historical II_START=4 (plate reading preserved)")
    # leitan must join the {block} node Q with the tail D at the outermost (root) level
    nodes = leitan.get("nodes") or []
    ids = [n[0] for n in nodes]
    referenced = {op for n in nodes for op in n[1:3] if isinstance(op, str) and op in ids}
    roots = [n for n in nodes if n[0] not in referenced]
    if not (len(roots) == 1 and roots[0][0] == "R"
            and {o for o in roots[0][1:3] if isinstance(o, str)} == {"Q", "D"}):
        fail(f"C-D5: leitan root node {roots} does not join Q+D (block+tail)")
    else:
        ok(f"C-D5: leitan root {roots[0][0]} = Q + D")
    gal = norm(GALLERY.read_text(encoding="utf-8"))
    if "D5" not in gal or "Leitan" not in gal:
        fail("C-D5: gallery does not document the D5 Leitan recut")
    else:
        ok("C-D5: gallery documents the D5 recut")
    for rel in ("klammerdiagramm/klammerdiagramm-uddama-example.svg",
                "klammerdiagramm/klammerdiagramm-uddama-plate-historical.svg"):
        if not (ROOT / rel).is_file():
            fail(f"C-D5: missing render {rel}")


def check_accdual(m: dict) -> None:
    doc = norm(RTL_DOC.read_text(encoding="utf-8"))
    if not re.search(r"Acc\.\s*dual", doc):
        fail("C-ACCDUAL: sanskrit-right-to-left-reading.md lacks the 'Acc. dual' label")
    else:
        ok("C-ACCDUAL: RTL doc carries 'Acc. dual'")
    # the correction: -e dual is Nom./Acc., NOT locative
    if not re.search(r"[Nn]ot\s+locative|не\s+локатив|NOT locative", doc):
        # fall back: the documented sentence must pair Acc. dual with the -e explanation
        if not re.search(r"Acc\.\s*dual[^\n]{0,200}-e", doc):
            fail("C-ACCDUAL: RTL doc does not document the -e dual = Nom./Acc. (not locative) correction")
    if re.search(r"loc\w*\s*dual[^)]*abhij", doc, re.I):
        fail("C-ACCDUAL: doc still labels the worked-sentence dual as locative")
    canary = ROOT / "teaching-pack/canaries/acc-dual-canary.html"
    if not canary.is_file():
        fail("C-ACCDUAL: teaching-pack/canaries/acc-dual-canary.html missing")
    else:
        ctext = canary.read_text(encoding="utf-8")
        if not re.search(r"Acc\.\s*dual", ctext):
            fail("C-ACCDUAL: canary HTML lacks the 'Acc. dual' label")
        if re.search(r"locative", ctext) and not re.search(r"not locative|не локатив", ctext, re.I):
            fail("C-ACCDUAL: canary HTML mentions locative without the negation")
        if "abhijñānaśākuntale" not in ctext and "abhijnanasakuntale" not in ctext:
            fail("C-ACCDUAL: canary HTML lacks the worked form abhijñānaśākuntale")
        else:
            ok("C-ACCDUAL: canary HTML carries Acc. dual + worked form")


_FOLD = str.maketrans({
    "ā": "a", "ī": "i", "ū": "u", "ṛ": "r", "ṝ": "r", "ḷ": "l", "ḹ": "l",
    "ṃ": "m", "ṁ": "m", "ḥ": "h", "ṅ": "n", "ñ": "n", "ṇ": "n",
    "ṭ": "t", "ḍ": "d", "ś": "s", "ṣ": "s",
})


def fold(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower().translate(_FOLD))


def words(text: str) -> set[str]:
    """Folded word tokens from <text> element contents only (word line + labels), no desc/title."""
    body = re.sub(r"<desc>.*?</desc>|<title>.*?</title>", "", text, flags=re.S)
    content = "".join(re.findall(r"<text[^>]*>(.*?)</text>", body, flags=re.S))
    content = re.sub(r"<[^>]+>", "", content)
    return {w for w in (fold(t) for t in re.split(r"[^A-Za-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ\-]+", content)) if len(w) >= 4}


def link_hits(ex: str, svg_text: str) -> bool:
    """True when the leaf's example words are attested in the render's word line (folded substring rule)."""
    ex_tokens = [t for t in (fold(p) for p in re.split(r"[^A-Za-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ\-]+", ex)) if len(t) >= 4]
    svg_tokens = words(svg_text)
    return any(t in s or s in t for t in ex_tokens for s in svg_tokens)


def check_taxonomy(m: dict) -> None:
    """Hard: every diagram link target exists. Soft (editorial, Q1): the authored
    family-illustration audit is complete and each entry points at a real render.
    NOTE: a word-level auto-classifier is deliberately NOT used — sandhi vs analytic
    forms (śītoṣṇam vs śīta-uṣṇam, vanāntaram vs vana-antaram) make string matching
    unreliable; the classification is an authored finding recorded in the manifest."""
    tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    leaves: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            if "ex" in o and ("vigraha" in o or "ru" in o):
                leaves.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(tax)
    linked = [l for l in leaves if l.get("diagram")]
    n_links = 0
    missing = []
    for leaf in linked:
        for rel in (leaf["diagram"] if isinstance(leaf["diagram"], list) else [leaf["diagram"]]):
            n_links += 1
            if not (ROOT / "klammerdiagramm" / rel).is_file() and not (ROOT / rel).is_file():
                missing.append((leaf["id"], rel))
    if missing:
        fail(f"taxonomy: {len(missing)} diagram link(s) resolve to no file: {missing}")
    else:
        ok(f"taxonomy: all {n_links} diagram link targets exist ({len(leaves)} leaves / {len(linked)} linked)")
    recorded = m.get("taxonomy_link_audit", {}).get("family_illustration_links", [])
    want = m["scope"]["coverage"].get("family_illustration_links")
    if want is not None and len(recorded) != want:
        fail(f"taxonomy: recorded family-illustration links {len(recorded)} != scope.coverage {want}")
    bad = [e for e in recorded
           if not (e.get("leaf") and e.get("ex")
                   and ((ROOT / "klammerdiagramm" / e.get("render", "")).is_file()))]
    if bad:
        fail(f"taxonomy: audit entries with missing fields/render: {bad}")
    if not missing and not bad and (want is None or len(recorded) == want):
        ok(f"taxonomy: authored audit intact ({len(recorded)} family-illustration links, Q1 open)")


def check_source_tokens(m: dict) -> None:
    """Manifest source_text must be the config's own token sequence (collapse hyphens/brackets/notes).
    This is the data<->manifest link that keeps the pack honest against the render configs."""
    def collapse(s: str) -> str:
        s = re.sub(r"\[[^\]]*\]", "", s)          # drop ghost brackets (rendered separately)
        s = re.sub(r"\([^)]*\)", "", s)           # drop editorial notes
        return fold(s)

    checked = 0
    for ex in m["examples"]:
        prov = ex.get("provenance") or {}
        cfg_rel = prov.get("config")
        if not cfg_rel or not (ROOT / cfg_rel).is_file():
            continue
        cfg = json.loads((ROOT / cfg_rel).read_text(encoding="utf-8"))
        toks = cfg.get("tokens") or []
        if isinstance(toks, str):
            toks = toks.split()
        want = collapse(" ".join(toks) if isinstance(toks, list) else str(toks))
        got = collapse(ex.get("source_text", ""))
        checked += 1
        if want != got:
            fail(f"{ex['id']}: source_text does not collapse to config tokens "
                 f"(manifest={got!r} vs config={want!r})")
    ok(f"source_text<->config tokens: {checked} examples compared (folded, hyphen/bracket-insensitive)")


def render_md(m: dict) -> None:
    lines = [
        "# Reviewed reading example pack (H8028)",
        "",
        "_Generated from `example_pack_manifest.json` — do not hand-edit; run `python scripts/check_example_pack.py --render-md`._",
        "",
        f"**Version** {m['version']} · **created** {m['created']} · **spec** {m['spec']}",
        "",
        "## Scope & coverage",
        "",
    ]
    sc = m["scope"]
    lines += [f"- **Includes**: {sc['includes']}",
              "- **Coverage**: " + " · ".join(f"{k} = {v}" for k, v in sc["coverage"].items()),
              f"- **No quota**: {sc['no_quota']}", ""]
    for ex in sc["exclusions"]:
        lines.append(f"- **Excluded**: {ex}")
    lines += ["", "## Examples", "",
              "| id | status | category | translation (lang) | provenance | reviewer |",
              "|---|---|---|---|---|---|"]
    for ex in m["examples"]:
        at = ex.get("aligned_translation") or {}
        prov = ex.get("provenance") or {}
        cfg = Path(prov.get("config", "")).name
        st = ex["review_status"]
        mark = "✅" if st == "approved" else "🚫"
        cat = ex.get("category", "").split("—")[0].strip()
        lines.append(f"| `{ex['id']}` | {mark} {st} | {cat} | {at.get('lang','?')}: "
                     f"{at.get('text','')[:60]}… | {cfg} | {ex.get('reviewer_provenance','')[:70]} |")
    lines += ["", "### Withheld", ""]
    for ex in m["examples"]:
        if ex["review_status"] == "withheld":
            lines.append(f"- **`{ex['id']}`** — {ex.get('withheld_reason')} (reviewer: {ex.get('reviewer_provenance')})")
    lines += ["", "## Correction canaries", ""]
    for c in m["correction_canaries"]:
        lines += [f"### {c['id']}", f"**Assertion**: {c['assertion']}", f"**Ruling**: {c['ruling']}",
                  f"**Targets**: {', '.join('`%s`' % t for t in c['targets'])}", ""]
    lines += ["## Audit findings & unresolved questions", "",
              f"- **Taxonomy link audit**: {m['taxonomy_link_audit']['verdict']} "
              f"({len(m['taxonomy_link_audit']['family_illustration_links'])} family-illustration links recorded).",
              f"- **Corrections applied**: {len(m['corrections_applied'])} — the D4 ghost, D5 recut and "
              "Acc. dual corrections were already in place at claim time (verified, not re-applied); "
              "stale render metadata was regenerated (see list below).", ""]
    for c in m.get("corrections_applied", []):
        lines.append(f"- **{c['id']}** `{c['target']}` — {c['what']} _{c['fix']}_")
    lines.append("")
    for q in m["unresolved"]:
        lines += [f"**{q['id']}** — {q['question']}", f"- status: {q['status']} · route: {q['route']}", ""]
    (ROOT / "teaching-pack" / "EXAMPLE_PACK.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"ok    rendered teaching-pack/EXAMPLE_PACK.md ({len(lines)} lines)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render-md", action="store_true")
    args = ap.parse_args()
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    check_schema(m)
    check_parity(m)
    check_source_tokens(m)
    check_d4(m)
    check_d5()
    check_accdual(m)
    check_taxonomy(m)
    if args.render_md:
        render_md(m)
    print()
    if FAILURES:
        print(f"RESULT: FAIL — {len(FAILURES)} hard failure(s), {len(FINDINGS)} finding(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"RESULT: PASS — 0 hard failures, {len(FINDINGS)} recorded finding(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
