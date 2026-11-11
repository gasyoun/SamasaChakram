# Reviewed reading example pack (H8028)

_Generated from `example_pack_manifest.json` — do not hand-edit; run `python scripts/check_example_pack.py --render-md`._

**Version** 0.1.0 · **created** 2026-11-11 · **spec** Uprava handoff H8028 (class: data, gate: none) — source-linked reviewed compound teaching pack for the first reading pilot

## Scope & coverage

- **Includes**: All 20 committed klammerdiagramm render configs (config + SVG + HTML + PNG) as the rendered reading subset, cross-linked to their samasacakra-taxonomy.json leaves where the leaf example matches the rendered compound.
- **Coverage**: rendered_examples = 20 · taxonomy_leaves = 58 · taxonomy_leaves_with_diagram_link = 17 · family_illustration_links = 8 · correction_canaries = 3
- **No quota**: No example count, lesson count or effectiveness threshold is invented here; coverage is exactly what the repository already renders (20) and what the wheel already carries (58 leaves).

- **Excluded**: 41 taxonomy leaves without a rendered diagram — wheel examples only, not yet drawn; not part of the rendered reading subset.
- **Excluded**: klammerdiagramm-uddama-plate-historical — superseded reading (MG vote D5, 16-07-2026); retained as geometry-calibration reference, withheld from the lesson subset.
- **Excluded**: Taxonomy diagram links whose linked render does not contain the leaf's example word (family/type illustrations) — recorded as audit findings under `taxonomy_link_audit`, not treated as example provenance.

## Examples

| id | status | category | translation (lang) | provenance | reviewer |
|---|---|---|---|---|---|
| `uddama-leitan` | ✅ approved | mixed | ru: природа которой подобна [природе] Луны для массы тьмы, котор… | klammerdiagramm-uddama-leitan.json | MG vote D5, 16-07-2026 (H997); gallery §1 (klammerdiagramm-worked-exam |
| `uddama-plate-historical` | 🚫 withheld | pure right-branching chain (superseded by D5) | ru: (same strophe as uddama-leitan — translation rides on the ca… | klammerdiagramm-uddama-plate-historical.json | plate signed off 15-07-2026 (1:1); superseded by MG vote D5, 16-07-202 |
| `abhijnanasakuntalam` | ✅ approved | tatpuruṣa title compound (first member = dvandva) | ru: узнавание и Шакунтала («Абхиджняна-Шакунтала»)… | klammerdiagramm-abhijnanasakuntalam.json | gallery §2 (asked — degenerate but confirmed); case-label correction d |
| `rajarsivamsah` | ✅ approved | karmadhāraya (appositional) inside tatpuruṣa | ru: царь-провидец… | klammerdiagramm-rajarsivamsah.json | gallery §3 (nesting ASKED and confirmed); taxonomy leaf appositional |
| `hastyasvarathaghosah` | ✅ approved | dvandva block + tatpuruṣa head | en: the din of elephants, horses and chariots… | klammerdiagramm-hastyasvarathaghosah.json | gallery §4 (II часть asked — a valid answer); MG dvandva law 15-07-202 |
| `sitosnasukhaduhkhadah` | ✅ approved | dvandva of dvandvas + upapada-tatpuruṣa head | en: giving cold-and-heat, pleasure-and-pain… | klammerdiagramm-sitosnasukhaduhkhadah.json | gallery §5 (asked; flat four-member alternative recorded) |
| `cakrapanicaranakamalasevaphalam` | ✅ approved | bahuvrīhi (locative vyadhikaraṇa) + karmadhāraya + tatpuruṣa spine | ru: с диском в руке (Вишну) — [плод] служения лотос-стопам… | klammerdiagramm-cakrapanicaranakamalasevaphalam.json | gallery §6 (nesting ASKED); taxonomy leaf loc-bv |
| `sankhacakragadapanicaranakamalaseva` | ✅ approved | dvandva + bahuvrīhi + karmadhāraya + tatpuruṣa in one word | en: service to the lotus-feet of the Conch-Discus-Mace-Handed… | klammerdiagramm-sankhacakragadapanicaranakamalaseva.json | gallery §7 (nesting ASKED) |
| `sankhabherinadahastyasvaghosapurnanagaram` | ✅ approved | two dvandva blocks + dvandva-of-tatpuruṣas + tatpuruṣa chain | en: the city filled with the sound of conches-and-kettledrums an… | klammerdiagramm-sankhabherinadahastyasvaghosapurnanagaram.json | gallery §8 (nesting ASKED) |
| `yathasaktidattannapanadanapunyaphalabhagi` | ✅ approved | avyayībhāva + dvandva + karmadhāraya + tatpuruṣa + upapada head | ru: по силам… | klammerdiagramm-yathasaktidattannapanadanapunyaphalabhagi.json | gallery §9 (nesting and II часть ASKED); MG avyayībhāva ruling 15-07-2 |
| `yathavidhigandhapuspanilakanthapadapadmapujaphalam` | ✅ approved | all five samāsa kinds | en: the fruit of the worship, performed according to rule with i… | klammerdiagramm-yathavidhigandhapuspanilakanthapadapadmapujaphalam.json | gallery §10 (nesting and II часть ASKED per contract) |
| `yatpadambhojasevarucisucimanasam` | ✅ approved | upamita pair inside a right-branching chain (bahuvrīhi protasis, yat-) | ru: за счёт светa служения стопам-лотосам которой чистотой восси… | klammerdiagramm-yatpadambhojasevarucisucimanasam.json | comparison §3.3 (II часть asked); source strophe pinned in the Leitan  |
| `janmarogamaranadi` | ✅ approved | X-ādi bahuvrīhi over a dvandva block | ru: такое бытие, начальные элементы которого — это рождение, бол… | klammerdiagramm-janmarogamaranadi.json | comparison §3.1 (II часть asked); Leitan conspectus vigraha + RU trans |
| `pancagavadhana` | ✅ approved | dvigu (karmadhāraya subtype) inside tatpuruṣa | ru: чьё богатство — пять коров… | klammerdiagramm-pancagavadhana.json | MG vote D1, 16-07-2026 (H997); comparison §3.2; gallery §3.2 |
| `tribhuvana` | ✅ approved | dvigu samāhāre (collective) | ru: троемирье… | klammerdiagramm-tribhuvana.json | MG vote D1, 16-07-2026 (H997); taxonomy leaf samahare-dvigu |
| `panipadamukha` | ✅ approved | samāhāra-dvandva (collective) | ru: руки, ноги и лицо (вместе)… | klammerdiagramm-panipadamukha.json | MG vote D2, 16-07-2026 (H997); taxonomy leaf samahara-dv |
| `rajadanta` | ✅ approved | ekadeśin / prathamā-tatpuruṣa | ru: передний зуб… | klammerdiagramm-rajadanta.json | MG vote D3, 16-07-2026 (H997); taxonomy leaf ekadesin |
| `vanantara` | ✅ approved | mayūravyaṃsakādi / X-antara bahuvrīhi | ru: другой лес… | klammerdiagramm-vanantara.json | MG vote D3, 16-07-2026 (H997); taxonomy leaf mayura |
| `sitosna` | ✅ approved | viśeṣaṇobhayapada-karmadhāraya | ru: тепло-холодная [вода]… | klammerdiagramm-sitosna.json | MG vote D6, 16-07-2026 (H997); taxonomy leaf ubhayapada |
| `sakapriyaparthivah` | ✅ approved | tatpuruṣa · madhyamapadalopin (elided middle member) | ru: царь-любитель овощей… | klammerdiagramm-sakapriyaparthivah.json | MG vote D4, 16-07-2026 (H997, corrected same day); gallery §11 |

### Withheld

- **`uddama-plate-historical`** — superseded constituency (D5) — geometry reference only, not an approved lesson example (reviewer: plate signed off 15-07-2026 (1:1); superseded by MG vote D5, 16-07-2026 (H997))

## Correction canaries

### C-D4-ghost
**Assertion**: The supplied [priya] of D4 is visibly editorial: rendered in square brackets in the word line, measured into the run, with no bar, no arrows and no node index — not an ordinary constituent, not footnote-only.
**Ruling**: D4 (MG 16-07-2026, H997)
**Targets**: `klammerdiagramm/klammerdiagramm-sakapriyaparthivah.json`, `klammerdiagramm/klammerdiagramm-sakapriyaparthivah-example.svg`, `klammerdiagramm/klammerdiagramm-sakapriyaparthivah-example.html`

### C-D5-uddama
**Assertion**: The canonical uddama grouping is Leitan's {uddāma-ajñāna-rūpa} block + tail with the ‖-mark/II-часть before svabhāvā; the signed-off plate reading stays reproducible as klammerdiagramm-uddama-plate-historical.
**Ruling**: D5 (MG 16-07-2026, H997)
**Targets**: `klammerdiagramm/klammerdiagramm-uddama-leitan.json`, `klammerdiagramm/klammerdiagramm-uddama-example.svg`, `klammerdiagramm/klammerdiagramm-uddama-plate-historical.json`, `klammerdiagramm/klammerdiagramm-uddama-plate-historical.svg`

### C-ACCDUAL
**Assertion**: The -e dual of the worked sentence (abhijñānaśākuntale) is labelled Acc. dual (Nom./Acc.), never locative — the documented correction in sanskrit-right-to-left-reading.md §Discipline — and the label survives browser and print rendering of the canary.
**Ruling**: documented correction, sanskrit-right-to-left-reading.md §Discipline (updated 05-09-2026)
**Targets**: `sanskrit-right-to-left-reading.md`, `teaching-pack/canaries/acc-dual-canary.html`

## Audit findings & unresolved questions

- **Taxonomy link audit**: Recorded, not corrected — whether these links are deliberate family illustrations or stale pointers is an editorial question for MG (see unresolved Q1). (8 family-illustration links recorded).
- **Corrections applied**: 2 — the D4 ghost, D5 recut and Acc. dual corrections were already in place at claim time (verified, not re-applied); stale render metadata was regenerated (see list below).

- **R1** `klammerdiagramm/klammerdiagramm-uddama-example.{svg,html}` — stale render metadata — the committed SVG/HTML carried the pre-D5 generic <desc> while klammerdiagramm-uddama-leitan.json carried the post-D5 Leitan description; geometry was already correct (metadata-only drift, caught by scripts/check_example_pack.py parity). _regenerated from klammerdiagramm-uddama-leitan.json with the committed builder, CRLF->LF normalised to the repo's .gitattributes policy; PNG untouched (desc/title are not painted)._
- **R2** `klammerdiagramm/klammerdiagramm-uddama-plate-historical.{svg,html}` — stale render metadata — the committed render carried the generic default description while klammerdiagramm-uddama-plate-historical.json carried the HISTORICAL/superseded-reading provenance description. _regenerated from klammerdiagramm-uddama-plate-historical.json the same way; geometry unchanged._

**Q1** — Are the 8 taxonomy `diagram` links whose render does not contain the leaf's own example word deliberate family/type illustrations, or stale pointers? (taxonomy_link_audit.family_illustration_links)
- status: open — recorded, not resolved by guess (H8028 stop-budget) · route: editorial decision (@DECIDE class) before any taxonomy edit

**Q2** — aligned_translation language mix: 6 approved examples currently carry an EN gloss (gallery-sourced) rather than a RU translation — hastyasvarathaghosah, sitosnasukhaduhkhadah, sankhabheri, sankhacakragada, yathavidhi, abhijnanasakuntalam (partial RU). Is EN acceptable for the pilot lessons, or must every approved example be RU-aligned first?
- status: open — no language quota invented (H8028: no invented quota) · route: methodolog/pilot decision before lesson publication

**Q3** — The H1298 attested gold ladder (30 corpus-attested compounds, SanskritGrammar) is not yet cross-linked into this pack — reuse requires a provenance-mapped join (gold-ladder id ↔ pack example id), not a copy.
- status: open — pending the SanskritGrammar-side registry (H1298 archive) · route: follow-up handoff; do not copy gold rows without provenance

