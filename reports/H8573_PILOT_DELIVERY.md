# H8573 — five-lesson pilot: delivery evidence

_Created: 24-11-2026 · Handoff: [H8573](https://github.com/gasyoun/Uprava/blob/main/handoffs/H8573-DeepSeek_SamasaChakram_drumam-five-lesson-pilot_24.11.26.md) · Executor: DeepSeek V4.1 Flash 1017 (deepseek-flash), Windows_

Approved design: branch `design/drumam-wheel` at `d3108f7` —
[reports/DRUMAM_WHEEL_DESIGN_24-11-2026.md](https://github.com/gasyoun/SamasaChakram/blob/design/drumam-wheel/reports/DRUMAM_WHEEL_DESIGN_24-11-2026.md),
[ADR 0001](https://github.com/gasyoun/SamasaChakram/blob/design/drumam-wheel/docs/adr/0001-leitan-source-and-editorial-differences.md) (conspectus is the primary source),
[ADR 0002](https://github.com/gasyoun/SamasaChakram/blob/design/drumam-wheel/docs/adr/0002-corpus-frequency-and-wheel-labels.md) (corpus share only on exact tag match),
[Lowe reading notes](https://github.com/gasyoun/SamasaChakram/blob/design/drumam-wheel/reports/SAMASA_LOWE_READING_NOTES.md),
[handbook sample](https://github.com/gasyoun/SamasaChakram/blob/design/drumam-wheel/reports/SAMASA_HANDBOOK_SAMPLE.md).
The design branch is a reference only: nothing was merged from it, its files are
re-stated here as data, not copied as pages.

## What shipped

| Path | What it is |
|---|---|
| `samasacakra/pilot_data.json` | the ONE source of pilot content: five lessons, corpus-share table, kevala entry, legacy-id aliases |
| `samasacakra/build_pilot.py` | generator: paragraph index from the conspectus DOCX + five lesson pages from `pilot_data.json` |
| `docs/paragrafy/index.html` | web paragraph index — 67 §§, 20 sections, one permanent anchor per § (`#p-4-1-1`) |
| `docs/uroki/index.html` | pilot contents |
| `docs/uroki/01-raja-bharya.html` | lesson 1 — rāja-bhāryā, two trees, one f-structure |
| `docs/uroki/02-vlozhennaya-dvandva.html` | lesson 2 — nested dvandva, Lowe (46)–(48) |
| `docs/uroki/03-ramesvarah.html` | lesson 3 — two contexts, two defensible analyses |
| `docs/uroki/04-prathama-ekadesin.html` | lesson 4 — prathamā / ekadeśin, pūrvakāyaḥ |
| `docs/uroki/05-kevala-samasa.html` | lesson 5 — kevala-samāsa, separate entry |
| `docs/drumam/index.html` | Drumam entry row: five lessons · paragraph index · wheel (a Drumam visitor reaches the pilot from inside Drumam) |
| `samasacakra/build_samasacakra.py` | wheel generator extended: leaf numbers, measured-share layer, kevala entry, id routing |
| `samasacakra/samasacakra-taxonomy.json` | merged leaf `prathama` (prathamā / ekadeśin), first in the case row, `legacy_ids: ["ekadesin"]` |
| `samasacakra/check_pilot.py` | acceptance checks — 260 assertions, fail-closed |
| `reports/H8573-evidence/*.png` | browser screenshots: the four share modes (no layer · traffic-light · hatch · outline), the kevala card, lesson 4 with feedback, the paragraph index |

Regenerated artifacts: `docs/index.html`, `samasacakra/samasacakra-wheel.html`,
`samasacakra/samasacakra-wheel.svg`, `samasacakra/samasacakra-poster.html`,
`samasacakra/samasacakra-poster.pdf` (A2, one page, headless Edge).

Two follow-through edits the rename forced, both verified in the same pass:
`samasacakra/samasa_subtype_jev_choice_probe.py` (`GOLD["rajadanta"]` → `prathama`)
and the teaching pack's provenance strings (`taxonomy leaf prathama (formerly ekadesin)`);
`scripts/check_example_pack.py` stays green.

## The five lessons and their sources

| № | Lesson | Leaf (wheel №) | Primary source | § |
|---|---|---|---|---|
| 1 | rāja-bhāryā: генитивная развёртка и два дерева | ṣaṣṭhī (6) | Lowe 2015, § 7, e98, (44)–(45); Warnemyr (3d) | 4.1.6 |
| 2 | Вложенная двандва: два татпуруши внутри координации | itaretara (31) | Lowe 2015, § 7, e98, (46)–(48); Warnemyr (1), (3d), (5) | 6.1, 4.1.6 |
| 3 | rāmeśvaraḥ: два контекста и два обоснованных разбора | ṣaṣṭhyartha-bv (30) | конспект §§ 4.1.6, 5.1.5, 9; ISCLS 2026 | 4.1.6, 5.1.5, 9 |
| 4 | prathamā / ekadeśin: pūrvakāyaḥ и партитивный генитив | prathamā / ekadeśin (1) | конспект § 4.1.1, (4.1.1.a), (4.1.1.c) | 4.1.1 |
| 5 | kevala-samāsa: вход вне четырёх классов | separate entry | конспект § 8, (8.1), (8.2) | 8 |

Every lesson shows the vigraha and a teaching scheme immediately; formal diagrams
are collapsed `<details>`, each labelled with its model (Warnemyr formula / LFG
c-structure / LFG f-structure / bracket scheme) and its source. Lowe's trees are
**teaching paraphrases**, not reproductions of the published figures.

Source checks run against the local primary copies, not memory:

- Warnemyr, `Compounds.html` — `S = X–Y`; tatpuruṣa (3a–3f) with the case index on
  the LEFT stem; bahuvrīhi (4a) `ᴳya Y [yathā] X asti`; nesting rule (5)
  «A compound can be part of a bigger compound». **Negative finding, recorded in
  lesson 4:** the ekadeśin partitive genitive sits on the RIGHT stem, so formula
  (3d) does not describe the type — the lesson states this instead of bending the
  formula.
- Lowe, `Language 91(3)` PDF, e98 — (44)/(45) two c-structures, one f-structure
  (`PRED ‘wife’`, `POSS [PRED ‘king’]`); (46) `[[adhara-vicaraṇa-]tp [daśana-darśane]tp]dd`
  «quivering of the lips and baring of the teeth» (NOM.DU); (47) c-structure,
  (48) f-structure with `NUM DUAL`, two independent `PRED`/`POSS` pairs.
- Kulkarni & Kumar 2013 — Table 5 (measured shares) **and Appendix A
  «A Compound Tagset»** (the 56-tag names), which is what the tag→leaf mapping is
  checked against:

| Tag | Appendix A name | Wheel leaf | Match |
|---|---|---|---|
| T6 | ṣaṣṭhī (tatpuruṣa) | `sasthi` — ṣaṣṭhī | exact |
| K1 | viśeṣaṇa-pūrvapada (karmadhāraya) | `visesanapurvapada` — viśeṣaṇa-pūrvapada | exact |
| Bs6 | ṣaṣṭhyartha (bahuvrīhi) | `sasthyartha` — ṣaṣṭhyartha | exact |
| Tn | nañ (tatpuruṣa) | `nan-tp` — nañ- | exact |
| U | upapada (tatpuruṣa) | `upapada` — upapada- | exact |

The mapping was verified against Appendix A before anything was assigned: each of
the five measured tags carries the article's own name, matches its wheel leaf
exactly, and no measured tag is attached to a group or to a leaf whose label
differs (the single group value in the table is a conspectus estimate, not a
measured tag).

## Corpus-share layer (reviewer ruling 24-11-2026)

The three visual bands and the fourth state are reserved for **measured shares that
match a leaf tag exactly**. The source has five such values, and the tag→leaf
mapping was verified against the article's own Appendix A before anything was
coloured — so exactly five of the 58 leaves carry colour:

| Wheel № | Leaf | Tag | Appendix A name | Measured share | Band | Rank |
|---|---|---|---|---|---|---|
| 6 | ṣaṣṭhī | T6 | ṣaṣṭhī (tatpuruṣa) | 40.56 % (26 097) | ≥ 5 % | 1 of 5 |
| 15 | viśeṣaṇapūrvapada | K1 | viśeṣaṇa-pūrvapada (karmadhāraya) | 12.29 % (7 909) | ≥ 5 % | 2 of 5 |
| 30 | ṣaṣṭhyartha-bv | Bs6 | ṣaṣṭhyartha (bahuvrīhi) | 6.39 % (4 113) | ≥ 5 % | 3 of 5 |
| 8 | nañ- | Tn | nañ (tatpuruṣa) | 5.9 % (3 801) | ≥ 5 % | 4 of 5 |
| 11 | upapada | U | upapada (tatpuruṣa) | 4.32 % (2 782) | 1–< 5 % | 5 of 5 |
| — | other 53 leaves | — | — | no measured tag | «нет сопоставимой доли» | — |

- **Rank is shown only on those five cards**, and the card states its meaning in
  place: «Корпусный ранг: N из 5 — место по доле среди тегов с измеренной долей, не
  среди всех подтипов (ADR 0002)». The page note carries the same sentence.
- **The `< 1 %` band has no member.** No measured tag falls below 1 %; the band
  stays in the legend and the page states why, instead of borrowing an estimate.
- **Conspectus § 14 estimates are notes, not marks.** `~1,6 %` (caturthī), `< 1 %`
  (saptamī), `~9 %` (itaretara), `~3 %` (samāhāra-dvandva) and the `~2,0 %`
  family-level value appear only as an italic card note starting «Оценка конспекта
  § 14:», each ending «Это не измеренная доля: в частотном слое значение не
  отмечается.» They carry no band, no colour and no rank; the group estimate sits
  on the avyayībhāva family card, never on its leaves.

## Verification (what was actually run)

```
python samasacakra/build_samasacakra.py   # wheel svg/html + docs/index.html + poster html
python samasacakra/build_pilot.py         # paragraph index (67 §§) + 5 lesson pages
python samasacakra/check_pilot.py         # 260/260 checks pass  (exit 0)
python scripts/check_example_pack.py      # PASS — 0 hard failures
```

`check_pilot.py` asserts, among others: 58 unique leaf numbers; every segment's
`data-band` equals its published entry and **exactly the five measured shares are
banded**; every banded segment has a measured share behind it and no estimate
carries a band; each measured card shows its rank *and* the sentence that says what
the rank ranks among; no rank appears where no measured share exists; every § 14
estimate is present as its own note and none is dressed as a measured share; the
alias map resolves `ekadesin` to the merged leaf; no dead leaf id survives in the
JEV probe's gold map; every lesson § exists in the conspectus and every § anchor
exists in the index; each lesson names model + source on every diagram; each
exercise has an answer, a reason for every wrong option, an explanation and an
existing §; the Drumam page links the lessons, the index and the wheel; every
relative link on every generated page resolves.

Browser smoke (Playwright, Chromium, `http://127.0.0.1:8766` over `docs/`):

| Probe | Result |
|---|---|
| leaf numbers before / after light / hatch / outline | identical `1..58` in all four states |
| banded segments as rendered | `6·gte5`, `8·gte5`, `11·mid15`, `15·gte5`, `30·gte5` — 5 banded, 53 `none`, 58 segments |
| legend | 4 swatches, re-encoded per mode; hidden when no layer is on |
| `#k=ekadesin` (legacy id) | opens № 1 «prathamā / ekadeśin», pūrvakāyaḥ, § 4.1.1 |
| `#k=tatpurusa--vibhakti--sasthi` | opens № 6 with 40.56 %, rank 1 of 5, § link, lesson link |
| `#k=kevala` | opens the kevala card with § 8 and lesson 5 |
| lesson 4 exercise → «Проверить» | feedback becomes visible, verdict «Верно.» |
| poster | 1 page, A2 (1191×1684 pt), leaf colours intact, numbers drawn |

Screenshots: `reports/H8573-evidence/01…05, 07, 08`. A leaf-card screenshot was
withdrawn rather than shipped stale: the card gained the rank line after the last
capture, and the rank is asserted mechanically instead.

Console: one benign `favicon.ico` 404 on the local probe server (the site ships no
favicon); no script errors.

## Risks and residuals

1. **The conspectus contradicts itself on the denominator.** § 14 heads its
   frequency column «% корпуса (UoHyd)» and describes the sample as n = 9952,
   while the five figures it quotes are exactly Table 5 of Kulkarni & Kumar over
   ~64 000 compounds. The pilot publishes the Table-5 provenance for those five and
   treats every other § 14 value as an estimate; the discrepancy is reported, not
   silently resolved. Follow-up: an editorial note in the conspectus.
2. **Lowe (46) loses diacritics in the extracted PDF text** («daana- darane»);
   the printed compound is taken from tree (47) (`daśana-`, `darśane`) and the
   lesson says so. Worth a print check if the compound ever becomes a gallery item.
3. **The Drumam page is hand-maintained.** The link row was added to
   `docs/drumam/index.html` (the live Pages copy, 334 KB). No generator exists for
   it in-repo, and `drumam/archive/samasa_decision_tree.html` is the superseded
   import, so it was deliberately left untouched. Any future Drumam regeneration
   must preserve the `#pilot-links` block.
4. **Poster PDF is a render step.** `build_samasacakra.py` writes the poster HTML;
   the PDF is produced by headless Edge (`--headless=new --print-to-pdf`) and must
   be re-rendered whenever the taxonomy changes.
5. **Scope.** Full-wheel per-leaf markup, a dedicated Drumam branch for kevala, and
   the exhaustive literature review stay out of this pilot, as the handoff states.
   The 53 unbanded leaves are the visible reminder that the corpus evidence is thin.
