# Nightly bug hunt — SamasaChakram, 28-11-2026

_Created: 28-11-2026 · Last updated: 28-11-2026_

_Dr. Mārcis Gasūns_

Nightly, one repo, auto-fix HIGH (MG ruling 26-09-2026). Read-only static hunt
over all first-party code on `origin/main` @ `72fce6f` (H8638): `samasacakra/`
(incl. the whole `samasacakra/top1000/` module landed 25-11..27-11), `scripts/`,
`klammerdiagramm/*.py`, `drumam/data/avyaya_list.js` — 16 Python sources
(~6.6k lines) + the generated-page JS embedded in `build_samasacakra.py` /
`build_samasa_indexes.py`. Vendored copies, lockfiles, `node_modules`, data
giants, fonts and PNGs skipped. No `stenogrammy/` paths exist in this repo —
the fence holds trivially. Hunt ran in a claimed worktree off `origin/main`;
the shared main tree was never edited.

**Verdict: no HIGH findings. 4 MEDIUM, 6 LOW. Auto-fix not triggered (ruling
fixes HIGH code bugs only). No committed secrets, no credential/infra finding,
hence no GTD @DO row.**

---

## Findings

### MEDIUM

**M1 · Cyrillic section headings collapse to 8 duplicate bare `id="sec-"`
anchors on the published paragraph index**
[build_pilot.py L206](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/build_pilot.py#L206)

The section-id slugifier keeps only `[a-z0-9]`; every Cyrillic heading is
stripped to nothing, so 8 sections share the same empty id — invalid HTML
(ids must be unique document-wide), and none of the 8 sections can be
deep-linked (first occurrence wins). Latin-transliterated headings
(`iv-avyay-bh-va`) do get ids, so the defect is invisible until a pure-Cyrillic
heading appears. `check_pilot.py` does not catch it: it counts only the §
anchors (`p-<n>`), which are unaffected.

Evidence (live, this run): re-generated `docs/paragrafy/index.html` and grepped —
`8 × id="sec-"`; reproduced from the conspectus DOCX: the collapsing headings
are «Введение», «Левая и правая части: что допускается», «Указатель Б»,
«Указатель В», «Указатель Г», «Указатель Д», «Указатель Е», «Библиография».
Fix shape: transliterate Cyrillic in the slug (or fall back to `sec-<n>` /
heading hash) + a uniqueness assert in the builder.

**M2 · `_measure` crashes with a raw `KeyError` on any glyph outside the
committed Charis subset**
[build_klammerdiagramm.py L128](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/build_klammerdiagramm.py#L128)

`cmap[ord(c)]` has no fallback: one unmapped character anywhere in a config
token kills the whole render with `KeyError: <codepoint>`, naming neither the
character nor the token. The committed subset covers U+0020-007E, U+00A0-00FF,
U+0100-017F, U+1E00-1EFF, U+0400-045F, U+2010-2027; anything else (e.g. Latin
Ext-B `ǎ` U+01CE) crashes. The builder is the canonical CLI of
`/klammerdiagramm` and is routinely driven with fresh `--config` JSONs.

Evidence (live, this run):
`KeyError: 462` for token `śītǎn`; exit 1.

**M3 · `II_START == len(tokens)` → raw `IndexError` in both layout modes**
[build_klammerdiagramm.py L401](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/build_klammerdiagramm.py#L401)
·
[L406](https://github.com/gasyoun/SamasaChakram/blob/main/klammerdiagramm/build_klammerdiagramm.py#L406)

`II_START` is the first index of part II, so the off-by-one-prone value
`II_START = n` (part II empty) reaches `hyx[II_START - 1]` (tight, crash
guaranteed with `trailing_hyphen: false`, since only `n-1` hyphens exist) and
`cx[II_START]` (legacy). Both exit as bare `IndexError: list index out of
range` with no config validation message.

Evidence (live, this run): two probe configs (`II_START=2` of 2 tokens,
tight+`trailing_hyphen:false` and legacy `cx`), both `IndexError`, exit 1.

**M4 · chunk re-runs silently overwrite predictions (append + rank-keyed
last-wins)**
[chunked.py L59](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/chunked.py#L59)
·
[L70-L73](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/chunked.py#L70)

`chunk()` appends to `predictions.jsonl` in `"a"` mode; `assemble()` builds
`preds[p["rank"]] = p["pred"]`, so a duplicated rank silently takes the LAST
row. Re-running a chunk after a partial failure — or re-running it without
`--run` — leaves both the live and the new dry-run rows in the file, and the
published `top1000_typed.tsv` takes whichever came last with no warning, no
count of consumed/duplicated rows in the manifest. Kill-gate and sha pinning
still apply to the final artifact, so this is a provenance/corruption risk on
the pipeline path, not in the committed TSV (which checks green).

Evidence: code path audit; not executed live (pipeline inputs
`cmps.csv`/`word_frequency_norm.txt`/H989 gold are not in the repo — see L5).

### LOW

**L1 · `chunked.py prepare` with default flags crashes with a raw
`TypeError`** —
[chunked.py L125-L126](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/chunked.py#L125)
declare `--lemma-freq` / `--gold-base` optional with default `None`, but
`prepare()` (L20, L24) does `Path(None)` unguarded.
Evidence (live): `TypeError: expected str, bytes or os.PathLike object, not
NoneType`. The guarded entry is `run_pipeline.py` (flags required); `chunked.py`
is the resumable variant.

**L2 · dead first `rot` assignment in `tangential_label`** —
[build_samasacakra.py L196-L197](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/build_samasacakra.py#L196):
the L196 expression is overwritten by L197 unconditionally; only the L197 flip
rule is live. Output unaffected (regen is byte-identical).

**L3 · kevala §-anchor skips the `.`→`-` normalization used everywhere else** —
[build_samasacakra.py L333](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/build_samasacakra.py#L333)
builds `#p-{K["para"]}` raw, while L306 and `build_pilot.para_id()` normalize
`4.1.6 → 4-1-6`. Latent: `pilot_data.json` currently carries `para: "8"`
(dot-free), so all links resolve today; a future subsection § (e.g. `8.1`)
would produce a dead anchor silently.

**L4 · `route()` dies on a malformed hash** —
[build_samasacakra.py L702](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/build_samasacakra.py#L702):
`decodeURIComponent(location.hash)` throws `URIError` on a stray `%` (e.g.
`#k=100%`), aborting that navigation; later `hashchange` events still work.
Code-level (single navigation lost).

**L5 · committed top-1000 dataset is not re-derivable from the repo alone** —
[top1000/data](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/data)
commits only the outputs (`top1000_typed.tsv`, manifest, report); the inputs
(`cmps.csv`, `word_frequency_norm.txt`, `lemma_frequency.tsv`, H989 gold base)
and the intermediates (`fewshot.json`, `ranked.json`, `validation.json`,
`predictions.jsonl`) are absent, and
[chunked.py L20-L21](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/chunked.py#L20)
also re-computes the same seeded split twice. Output is sha256-pinned and the
report carries an honest tatpuruṣa-skew caveat, so this is provenance
completeness, not a data defect. Related footgun, documented by design:
[evaluate.py L14](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/evaluate.py#L14)
measures `coarse_accuracy` over scored items only, so with coverage < 1 the
kill-gate sees the easy subset (the committed run has coverage 1.000, so the
published 0.733 is unaffected).

**L6 · answer-validation mismatch between live parsing and the tree walker** —
[semantics.py L29-L32](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/semantics.py#L29)
accepts only option `next` ids, while
[classify.py L15-L16](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/top1000/classify.py#L15)
also accepts option labels. A live JEV answer carrying the human-readable label
is dropped as invalid (`unanswered`) even though the walker would have consumed
it — needless coverage loss, fail-soft.

---

## Not bugs (checked and cleared)

- No committed secrets: regex sweep over all code/config/workflow files
  (API-key/token/Bearer/AKIA/ghp_/sk- patterns) — only benign `tokens` config
  keys and env-file indirection (`jev_probe.resolve_config`, `.env` gitignored
  per the H4631 baseline).
- `changelog_released_headings.py` `strip('0 \t')` all-zero-sha trick — correct
  (strips only leading/trailing zeros; only an all-zero sha empties).
- `classify()` cycle guard via `seen` set; fail-soft `unknown` terminal.
- `build_top1000` SLP1 transliteration for frequency lookup — verified live:
  `rules.json` lists are IAST (`abhi`, `prati`, `yathā` present), so the
  avyaya/preverb form-node comparisons match IAST members; no SLP1/IAST
  mismatch (initial suspicion refuted by direct membership test).
- Wheel-page quiz/routing JS: pointer-capture retarget handled via `downSeg`;
  `ALIAS`/`cakra()` used before definition but hoisted; `setMode('none')`
  idempotent.

## What verified green (all live, this run)

- `pytest samasacakra/top1000/tests -q` — **43 passed**.
- `samasacakra/check_pilot.py` — **267/267 checks pass**.
- `samasacakra/check_quiz.py` — **PASS** (7 markers, 2 pages, 58+ leaves).
- `scripts/check_example_pack.py` — **PASS, 0 hard failures** (full data/render
  parity for every committed config, all canaries).
- `klammerdiagramm/check_historical_plate.py` — **PASS** (four bands, eight
  arrows, four rungs, seven labels, three elbows).
- `samasacakra/top1000/check_top1000.py` — **PASS** (sha256, 1000 rows, ranks
  1..1000 unique).
- `samasacakra/top1000/check_rules.py` — **PASS** (rules.json snapshot matches
  the drumam HTML).
- Byte-identical regeneration: `build_samasacakra.py`, `build_pilot.py`,
  `build_samasa_indexes.py` re-run in the worktree → `git status` clean (the
  committed artifacts match their generators exactly).

Environment note: the first `check_example_pack.py` run failed on every config
with `ImportError: No module named brotli` — a local-machine gap (fontTools
needs `brotli` to read WOFF2), not a repo defect; after `pip install --user
brotli` the gate passes. `requirements-test.txt` pins only the pytest closure;
a CI-side `brotli` pin is only needed if a parity check ever moves into CI.

## Disposition per the nightly ruling

- HIGH code bugs: **none found** → no auto-fix commit this run (MEDIUM/LOW are
  report-only per the ruling).
- HIGH credential/infra findings: **none** → no GTD @DO row minted.
- Suggested next units (not executed): fix M1 (slugifier + uniqueness check),
  M2/M3 (config validation in `build_klammerdiagramm.py`), M4 (idempotent
  predictions store).

Elapsed: ~40 min wall (hunt ≈ 30 min incl. live probes + full gate surface,
report + landing ≈ 10 min).
