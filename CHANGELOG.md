# Changelog — SamasaChakram

Dates are `DD-MM-YYYY` per the house convention.

_Created: 16-07-2026 · Last updated: 16-07-2026_

## [Unreleased]

## [0.2.1] - 2026-07-16

### Fixed — 16-07-2026 · D4 crosswalk-table consistency

- [`KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md`](https://github.com/gasyoun/SamasaChakram/blob/main/KLAMMERDIAGRAMM_LEITAN_SAMASA_COMPARISON.md)
  §2 coverage crosswalk still carried the pre-vote `🟨` snapshot for D1–D4, contradicting §4
  where all six are resolved. Flipped the five stale rows to ✅ and, for **D4**, corrected the
  substance: it framed the vote as "elided member has no bar" (the rejected footnote-only
  reading), whereas the actual **reject** («одной только сноски недостаточно») *restores* the
  elided member as an editorial ghost `śāka-[priya]-pārthivaḥ` (word line, no bar) — the
  `"ghosts"` generator key, gallery §11. The ghost-member notation itself was already built
  and migrated (claude-config v0.1.31 → v0.1.0 here); this only aligns the §2 table + bottom line.

## [0.2.0] - 2026-07-16

### Added — 16-07-2026 · H1016 · the samāsa-cakra wheel itself

- [`samasacakra/`](https://github.com/gasyoun/SamasaChakram/tree/main/samasacakra) — the
  repo's eponymous deliverable: a rotatable radial classification chart of the compound
  system. 4 classes (validated 4-hue categorical palette, light+dark both
  script-validated) · 10 families · 58 leaf subtypes, each with a canonical example from
  the Leitan conspectus; MG rulings annotated (right-to-left law, dvandva flat, D1–D6).
  Interactive HTML: embedded Klammer Serif, drag-to-rotate, click → vigraha + RU gloss
  panel, hover highlight, theme-aware. Generator + taxonomy JSON committed; PNG raster in
  the README.

## [0.1.0] - 2026-07-16

### Added — 16-07-2026 · H1010 · the samāsa programme consolidated here

- Migrated from claude-config (v0.1.31 state): the `/klammerdiagramm` generator with the
  OFL-renamed Charis 7.000 subset and the printed reference plate; the eleven-compound
  illustrated gallery; the shared right-to-left reading method with all MG rulings
  (samāsa direction · dvandva flat · avyayībhāva · D1–D6 of the Leitan crosswalk incl.
  the corrected D4 ghost-member notation); the H982 Leitan comparison report; and the
  pinned Leitan conspectus export (publication authorized by MG 16-07-2026). The three
  skills remain in claude-config and now point here.

_Dr. Mārcis Gasūns_
