# H8485 — gallery open-arrow repair + clean PNG export: evidence note

_Created: 20-11-2026 · Last updated: 20-11-2026_ — executor GLM 5.3 (glm-5.3), worker lane; visual review + git delivery: Codex.

## Source versus generated (provenance distinction)

- **Source original (frozen, byte-identical, sha256-pinned in
  [scripts/check_h8485_gallery.py](https://github.com/gasyoun/SamasaChakram/blob/main/scripts/check_h8485_gallery.py)):**
  [klammerdiagramm-target-plate.png](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-target-plate.png)
  — MG's printed-plate scan (recovered H814), the accepted 1213×723 Leitan source-plate
  reconstruction of merged PR #34, plus the historical-plate side:
  [config](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-uddama-plate-historical.json) ·
  [lettering](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-uddama-plate-lettering.json) ·
  [SVG](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-uddama-plate-historical.svg) ·
  [HTML](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-uddama-plate-historical.html) ·
  [PNG](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-uddama-plate-historical.png).
  **None of these were regenerated, edited or re-rendered.** The plate branch
  (`"plate"` configs → `_build_historical_plate`) is untouched code; its exact
  geometry was never transplanted into other words.
- **Generated (refreshed this pass):** the 19 non-plate SVG/HTML/PNG gallery
  triples — every one regenerated from its committed config by the shared
  builder and re-exported as PNGs from the SVG bounds. The old PNGs were NOT
  used as sources at any point.

## What changed in the shared renderer

[build_klammerdiagramm.py](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/build_klammerdiagramm.py)
(non-plate mode only):

1. **One open arrow per real visible member.** Each member draws a single
   OPEN (unfilled) chevron, apex at `ARROW_TIP`, aligned to the member's
   centre (metric grid), tail joined by one stem line into its hatched bar and
   on into the band. Removed: the legacy pair of filled edge-arrows and the
   two border stems protruding on either side of every member. Ghost members
   (`[priya]`, D4) draw no arrow/stem — structurally guaranteed: nodes
   reference real token indices only, ghosts carry no measured centre.
2. **Caption placement by measurement, not habit.** The I/II часть captions
   are measured (`Charis` advance widths) against their rule zones:
   - zone wide enough → **inline, legacy geometry byte-preserved**
     (identical x-centres to the pre-H8485 formula);
   - zone too narrow → the caption moves to its own aligned row above
     (y = 35, ogee tops at y = 52 — no vertical overlap), centred over its
     zone and clamped inside the canvas. The two collision cases —
     śīta-uṣṇa-sukha-duḥkha-dāḥ (right zone 10 px wide) and
     janma-roga-maraṇa-ādiḥ (27 px) — are raised; their ogee wings and the
     I-часть side keep the legacy geometry.

Constituent topology, dvandva leaf/block joins, tokens, labels and every
I/II split decision are unchanged: the node grammar and all 19 config JSONs
are byte-identical to the pre-H8485 state.

## PNG export

New [klammerdiagramm/export_png.py](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/export_png.py):
one persistent headless Google Chrome context
(`/Applications/Google Chrome.app/.../Google Chrome`, no downloads, throwaway
temp profile only), `colorScheme=light`, `deviceScaleFactor=1`, every request
that is not `file://`/`data:` blocked (fully offline), page chrome neutralised
(`main` margins/padding zeroed), and the screenshot cropped **exactly to the
`<svg>` element** → native viewBox dimensions, no browser chrome, no page
padding. Driver: the already-installed `playwright` python package used purely
as a CDP client to the system Chrome — no browser install, no extra profiles.

## Checks (all green, same worktree, Codex to reproduce)

| check | command | result |
|---|---|---|
| full teaching-pack validator + replay parity (20 pairs, LF-normalised) | `python scripts/check_example_pack.py` | PASS, 0 hard failures |
| H8485 mechanical gate (19 triples, arrows, ghosts, captions, PNG size/margins, frozen-plate sha256) | `python scripts/check_h8485_gallery.py` | PASS |
| baseline before any edit | `python scripts/check_example_pack.py` | PASS (recorded pre-repair) |
| frozen plate bytes | `shasum -a 256` vs pre-pass snapshot | identical (6 files) |

Representative diagrams first (checkpoint before the batch):
[abhijñāna-śākuntalam](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-abhijnanasakuntalam-example.png)
(two-member ∪), flat
[hasti-aśva-ratha-ghoṣaḥ](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-hastyasvarathaghosah-example.png),
nested
[śīta-uṣṇa-sukha-duḥkha-dāḥ](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/klammerdiagramm-sitosnasukhaduhkhadah-example.png)
(raised II часть) — all rendered and probed before the remaining 16 were
touched. Renderer iterations used: **1** (within the 2-iteration budget).

## The one classification correction

pañca-gava-dhanaḥ's teaching-pack category was recorded as "dvigu
(karmadhāraya subtype) inside **tatpuruṣa**" — wrong outer class: its own
vigraha (*pañca gāvo dhanaṃ yasya saḥ* — "whose wealth is five cows") and
[comparison §3.2](https://github.com/gasyoun/SamasaChakram/blob/main/KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md)
already call the outer compound a **bahuvrīhi**. Fixed in
[example_pack_manifest.json](https://github.com/gasyoun/SamasaChakram/blob/main/teaching-pack/example_pack_manifest.json)
(recorded as correction **R3**) and regenerated
[EXAMPLE_PACK.md](https://github.com/gasyoun/SamasaChakram/blob/main/teaching-pack/EXAMPLE_PACK.md).
The diagram, graph and all other lesson decisions unchanged.

## Limitations (honest residue)

- **Hatched bars lost their side-edge outlines** above the bands (the removed
  border stems doubled as bar edges). The bars are now defined by the hatch
  pattern alone; if Codex's visual review finds them too soft, restoring a
  bar-side outline *below* the arrow (not protruding above it) is the
  designated iteration-2 change — one `hline_clip`-style outline per bar.
- **Both-captions-raised is unhandled in practice**: if a hypothetical config
  raised BOTH часть captions onto the same row they could overlap; no gallery
  config reaches this (every I-часть zone fits inline — asserted by the gate),
  so it stays a recorded theoretical case, not code.
- **Caption legibility of the raised row** (y = 35, small 21 px type above the
  ogee) is a visual-judgment item for Codex/MG, not machine-verifiable.
- **Global skill doc still describes the old furniture**: `/klammerdiagramm`
  in claude-config says "two up-arrows each" — out of this handoff's edit
  scope (no global-skill edits); the repo-local rendering spec
  ([sanskrit-right-to-left-reading.md](https://github.com/gasyoun/SamasaChakram/blob/main/sanskrit-right-to-left-reading.md)
  §Publication-grade form) was updated instead. Follow-up for the claude-config
  side belongs to the verifier's delivery or a GTD row.
- PNG rendering is deterministic given the same Chrome + embedded WOFF2
  subset, but PNG bytes are not canonical across Chrome versions (SVG/HTML
  remain the byte-stable artifacts; PNGs are display renders).

_Dr. Mārcis Gasūns_
