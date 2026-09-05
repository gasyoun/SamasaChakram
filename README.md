# SamasaChakram

_Created: 11-07-2026 · Last updated: 05-09-2026_

> **Status: live.** The samāsa programme consolidated here 16-07-2026 (H1010) from
> claude-config: the /klammerdiagramm drawing system, its worked-example gallery,
> the shared right-to-left reading method, and the Leitan conspectus crosswalk.

## The wheel

![samāsa-cakra — the wheel of Sanskrit compounds](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/samasacakra-wheel.png)

**Live:** [gasyoun.github.io/SamasaChakram](https://gasyoun.github.io/SamasaChakram/) —
the wheel on GitHub Pages. **Interactive source:** [samasacakra/samasacakra-wheel.html](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/samasacakra-wheel.html)
(same page, open locally — drag to rotate, click a segment for the vigraha + Russian gloss — thirteen
leaves embed their Klammerdiagramm from the gallery right in the panel — every drawn
gallery compound is now reachable from the wheel, and every
leaf links to the gallery; double-click to reset; **IAST ⇄ Devanāgarī script toggle**, embedded Klammer Serif + Klammer Deva
(an OFL-renamed Noto Serif Devanagari subset — licence bundled), light/dark themes). **Print/poster export:** [samasacakra/samasacakra-poster.pdf](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/samasacakra-poster.pdf)
— a single A2 sheet (420×594 mm): dual-script title, the wheel full-width, and the complete
58-subtype index in four class columns (term — example in both scripts — RU gloss), with
the pradhāna line and MG structure rule heading each class. Built by
[samasacakra/build_samasacakra.py](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/build_samasacakra.py)
from [samasacakra/samasacakra-taxonomy.json](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/samasacakra-taxonomy.json) —
4 classes (Patañjali's pradhāna scheme) · 10 families · 58 leaf subtypes, each with a
canonical example from the Leitan conspectus; the MG structural rulings (right-to-left law,
dvandva the sole flat exception, D1–D6) annotated per class and leaf.

## Contents

| Path | What it is |
|---|---|
| [sanskrit-right-to-left-reading.md](https://github.com/gasyoun/SamasaChakram/blob/main/sanskrit-right-to-left-reading.md) | the canonical right-to-left (head-first) reading method + all MG samāsa-direction rulings; shared source for the `/sanskrit-parse`, `/klammeruebersetzung` and `/klammerdiagramm` skills (which live in [claude-config](https://github.com/gasyoun/claude-config)) |
| [klammerdiagramm-worked-examples.md](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm-worked-examples.md) | the illustrated gallery — eleven worked sections from the 2-lemma pair to the all-five-kinds capstone, each with diagram, config and what its run proved (19 drawn plates in all, counting the Leitan-comparison and D-vote examples) |
| [KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md](https://github.com/gasyoun/SamasaChakram/blob/main/KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md) | the H982 crosswalk of the drawing system against Э. З. Лейтан's samāsa conspectus, with the six voted rulings (D1–D6) applied |
| [klammerdiagramm/](https://github.com/gasyoun/SamasaChakram/tree/main/klammerdiagramm) | the generator ([build_klammerdiagramm.py](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/build_klammerdiagramm.py)), the OFL-renamed Charis 7.000 subset + licence, the printed reference plate, and every worked diagram (config JSON + SVG + embedded-font HTML + PNG) |
| [samasacakra/](https://github.com/gasyoun/SamasaChakram/tree/main/samasacakra) | the samāsa-cakra wheel itself — taxonomy JSON, generator, interactive SVG/HTML (IAST ⇄ Devanāgarī, 18 of 58 leaves carrying their own bracket plates), the A2 poster, the Pages source (`docs/`), and the OFL-renamed Klammer Deva subset (H1016–H1036) |
| [leitan/](https://github.com/gasyoun/SamasaChakram/tree/main/leitan) | pinned text export of Э. З. Лейтан, «Сложные слова в санскрите» (from MG's «Общество ревнителей санскрита» webinar; publication authorized by MG 16-07-2026 pending Leitan's own word) + the review-request letter **sent to Leitan 16-07-2026** — his reply governs corrections and the copy's fate |

## What this is

*Samāsa Cakra* («колесо композитов») is a traditional Sanskrit pedagogical device: a
chart, arranged as a wheel, for teaching the classification and analysis (*vigraha*) of
Sanskrit nominal compounds — *tatpuruṣa* (incl. *karmadhāraya* and *dvigu*), *bahuvrīhi*,
*dvandva*, *avyayībhāva*. This repo is that device reinvented digitally: the live wheel
above, regenerable end-to-end from one taxonomy file, plus the drawing system
(Klammerdiagramm), the reading method, and the scholarly crosswalk it is all built on.

## Provenance & rules of the road

- **Taxonomy**: Э. З. Лейтан, «Сложные слова в санскрите» (conspectus of MG's webinar
  programme), crosswalked in [KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md](https://github.com/gasyoun/SamasaChakram/blob/main/KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md).
- **Structural rulings (MG)**: every samāsa binds right-to-left (head last) — bahuvrīhi
  exocentricity and avyayībhāva first-member prominence are semantics, not bracket
  direction; the dvandva alone is flat; the six crosswalk votes D1–D6 (dvigu, samāhāra,
  ekadeśin, the ghost-member notation, the uddāma constituency per Leitan, śītoṣṇa-type)
  are applied throughout.
- **Fonts**: Klammer Serif (Charis 7.000 subset) and Klammer Deva (Noto Serif Devanagari
  subset) — both renamed per the OFL Reserved-Font-Name rules, licences bundled beside
  the subsets, provenance scripts committed.
- The three skills that *use* this material (`/sanskrit-parse`, `/klammeruebersetzung`,
  `/klammerdiagramm`) live in [claude-config](https://github.com/gasyoun/claude-config)
  and point here; the repo is wired into
  [Uprava/PROJECT_INTERLINKS.md](https://github.com/gasyoun/Uprava/blob/main/PROJECT_INTERLINKS.md)
  (consume, don't rebuild).

## Status

Live since 16-07-2026 (H1010 consolidation → H1016 wheel → H1017 Devanāgarī → H1020/H1026
panel plates → H1021 poster → H1025 D-vote plates → H1030 full gallery coverage → H1036
Pages). Current release: see [CHANGELOG.md](https://github.com/gasyoun/SamasaChakram/blob/main/CHANGELOG.md)
and the [releases page](https://github.com/gasyoun/SamasaChakram/releases).
**@WAITING**: review letter sent to Э. Лейтан 16-07-2026 — his corrections go into
[samasacakra/samasacakra-taxonomy.json](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/samasacakra-taxonomy.json)
(one rebuild refreshes the wheel, the Pages site and the poster); his word on the
conspectus copy is final. Session journal: [.ai_state.md](https://github.com/gasyoun/SamasaChakram/blob/main/.ai_state.md).

## License

Licensed under the [Apache License 2.0](https://github.com/gasyoun/SamasaChakram/blob/main/LICENSE).

_Dr. Mārcis Gasūns_
