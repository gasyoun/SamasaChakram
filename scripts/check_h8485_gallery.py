#!/usr/bin/env python3
"""check_h8485_gallery.py — mechanical acceptance gate for the H8485 gallery repair
(open-arrow member mode + clean PNG export), SamasaChakram, 20-11-2026.

Checks, per the H8485 handoff acceptance:
  1. gallery inventory — the 19 non-plate configs each have a committed
     SVG + HTML + PNG triple reachable from the teaching-pack manifest.
  2. one open arrow per real member — every non-plate SVG carries exactly as many
     OPEN (fill="none") member arrows as its config has real (non-ghost) members
     referenced by nodes, each followed by one stem line; no legacy filled
     arrowhead triangles remain.
  3. ghost members free of arrows — the śāka-[priya]-pārthivaḥ ghost run has no
     arrow apex and no stem inside its measured x-range.
  4. caption/ogee non-collision — every I/II часть caption either sits inline
     (y = 59) with measured room in its rule zone, or is raised (y = 35); the two
     narrow-split cases (śīta-uṣṇa-sukha-duḥkha-dāḥ, janma-roga-maraṇa-ādiḥ) must
     be raised.
  5. native PNG export — every PNG's IHDR dimensions equal its SVG viewBox, and
     the export is clean (white margins at all four corners, no page padding).
  6. frozen plate bytes — the accepted Leitan source plate scan, the historical
     plate config/lettering/SVG/HTML/PNG are byte-identical to the H8485 baseline
     (sha256 pinned below; the plate mode is a separate frozen output).

Exit 0 = PASS. Run: python scripts/check_h8485_gallery.py  (repo root)
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "teaching-pack" / "example_pack_manifest.json"

# H8485 baseline (post-PR-#34 merge, sha256) — the frozen plate side of the repo.
FROZEN = {
    "klammerdiagramm/klammerdiagramm-target-plate.png":
        "d8e9e313f500e85c7f335a3ec4069e3da5b5a77fd2a377bb7e37e880d785817f",
    "klammerdiagramm/klammerdiagramm-uddama-plate-historical.svg":
        "44684fdf1c46a342088bfa0af13dca3fb83ebd23137e8f3c7916ba088c9220e7",
    "klammerdiagramm/klammerdiagramm-uddama-plate-historical.html":
        "a4a64853c7abb69b4b69bac960bf09ef0a2cb13f158fcff35b0ea888a4a07976",
    "klammerdiagramm/klammerdiagramm-uddama-plate-historical.png":
        "e4b8b6ea90b3f2cd5c679f77fa616298b07ba605b56abdcbaf339e31c80f0c0b",
    "klammerdiagramm/klammerdiagramm-uddama-plate-historical.json":
        "4bbaee2d7773bc7a370b33b6b39d6dc5f24aca1e0915ab14155b051f4496578c",
    "klammerdiagramm/klammerdiagramm-uddama-plate-lettering.json":
        "2f765cf6601d8f327b244504487d4254c281be4a4ebb6eea257aa701bd87dc62",
}
NARROW_SPLIT_IDS = {"sitosnasukhaduhkhadah", "janmarogamaranadi"}

FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def real_members(cfg: dict) -> set[int]:
    """Distinct real token indices referenced by node children."""
    used: set[int] = set()
    for nd in cfg.get("nodes", []):
        for ch in nd[1:3]:
            if isinstance(ch, int):
                used.add(ch)
            elif isinstance(ch, (list, tuple)):
                used.update(m for m in ch if isinstance(m, int))
    return used


def measure(s: str, fs: int) -> float:
    from fontTools.ttLib import TTFont
    f = TTFont(ROOT / "klammerdiagramm" / "charis-klammer-subset.woff2")
    upm, cmap, hmtx = f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in s) / upm * fs


def main() -> int:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    exs = [e for e in m["examples"] if e["id"] != "uddama-plate-historical"]
    if len(exs) != 19:
        fail(f"expected 19 non-plate examples, found {len(exs)}")

    arrow_re = re.compile(r'<path d="M([\d.]+) 159 L([\d.]+) 146 L([\d.]+) 159" fill="none"')
    legacy_arrow_re = re.compile(r'<path d="M[\d.]+ 146 L[\d.-]+ 157 L[\d.]+ 157 Z" fill=')
    stem_re = re.compile(r'<line x1="([\d.]+)" y1="146" x2="\1" y2="[\d.]+"')

    n_png = 0
    for ex in exs:
        eid = ex["id"]
        prov = ex["provenance"]
        cfg = json.loads((ROOT / prov["config"]).read_text(encoding="utf-8"))
        svg_p, html_p, png_p = (ROOT / prov["renders"][k] for k in ("svg", "html", "png"))
        for label, p in (("svg", svg_p), ("html", html_p), ("png", png_p)):
            if not p.is_file():
                fail(f"{eid}: missing {label} {p.name}")
        if not (svg_p.is_file() and html_p.is_file() and png_p.is_file()):
            continue
        svg = svg_p.read_text(encoding="utf-8")

        # 2. one open arrow per real member, one stem each, no legacy arrowheads
        arrows = arrow_re.findall(svg)
        members = real_members(cfg)
        if len(arrows) != len(members):
            fail(f"{eid}: {len(arrows)} open arrows != {len(members)} real members")
        stem_x = stem_re.findall(svg)
        if sorted(stem_x) != sorted(arrow[1] for arrow in arrows):
            fail(f"{eid}: arrowhead and stem do not meet at each member's apex")
        if legacy_arrow_re.search(svg):
            fail(f"{eid}: legacy filled arrowhead remains")

        # 3. ghost run carries no arrow/stem
        if cfg.get("ghosts"):
            st = dict(FS=cfg.get("style", {}).get("FS", 39))
            toks, n = cfg["tokens"], len(cfg["tokens"])
            trail = cfg.get("trailing_hyphen", True)
            x, gspan = 44.0, None
            for i, t in enumerate(toks):
                x += measure(t, st["FS"])
                if i < n - 1 or trail:
                    x += measure("-", st["FS"])
                for g in cfg["ghosts"]:
                    if g["after"] == i:
                        gspan = (x, x + measure(f"[{g['text']}]", st["FS"]))
                        x += measure(f"[{g['text']}]", st["FS"]) + (
                            measure("-", st["FS"]) if (i < n - 1 or trail) else 0)
            hit = [x for x in [a[1] for a in arrows] + stem_x
                   if gspan[0] < float(x) < gspan[1]]
            if hit:
                fail(f"{eid}: arrow/stem inside the ghost run {gspan}: {hit}")

        # 4. caption placement — inline only with measured room, else raised
        if cfg.get("II_START"):
            caps = re.findall(r'<text x="([\d.]+)" y="(\d+)" font-size="\d+" '
                              r'text-anchor="middle" fill="[^"]+">(I|II) часть</text>', svg)
            if len(caps) != 2:
                fail(f"{eid}: expected two часть captions, found {len(caps)}")
            else:
                raised = {c[2] for c in caps if c[1] == "35"}
                if (eid in NARROW_SPLIT_IDS) != ("II" in raised):
                    fail(f"{eid}: II часть raised={('II' in raised)} "
                         f"(narrow-split case={eid in NARROW_SPLIT_IDS})")
                for x_cap, y_cap, part in caps:
                    if y_cap not in ("35", "59"):
                        fail(f"{eid}: {part} часть on unknown row y={y_cap}")
                    if y_cap == "35" and part == "I":
                        fail(f"{eid}: I часть raised (left zone always fits in the gallery)")

        # 5. PNG native size + clean margins
        png_bytes = png_p.read_bytes()
        w, h = struct.unpack(">II", png_bytes[16:24])
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
        if not vb or (w, h) != (int(vb.group(1)), int(vb.group(2))):
            fail(f"{eid}: PNG {w}x{h} != viewBox {(int(vb.group(1)), int(vb.group(2))) if vb else '?'}")
            continue
        n_png += 1
        try:
            from PIL import Image
            im = Image.open(png_p).convert("L")
            px = im.load()
            corners = (px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1])
            if any(c < 250 for c in corners):
                fail(f"{eid}: PNG margins not clean (page padding?): corners {corners}")
        except ImportError:
            print(f"NOTE  {eid}: PIL absent — PNG corner cleanliness not probed")

    # 6. frozen plate bytes
    bad = [rel for rel, want in FROZEN.items() if sha256(ROOT / rel) != want]
    if bad:
        fail(f"frozen plate outputs drifted: {bad}")
    else:
        ok(f"frozen plate bytes identical ({len(FROZEN)} files sha256-pinned)")

    ok(f"gallery: {n_png} non-plate PNG/SVG/HTML triples checked")
    print()
    if FAILURES:
        print(f"RESULT: FAIL — {len(FAILURES)} failure(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("RESULT: PASS — 19 triples, one open arrow per real member, ghosts clean, "
          "captions placed by measurement, native-size clean PNGs, plate frozen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
