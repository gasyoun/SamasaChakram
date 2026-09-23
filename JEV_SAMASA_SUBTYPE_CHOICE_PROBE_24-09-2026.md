_Created: 24-09-2026 · Last updated: 24-09-2026_

# H5278 — Jev choice probe: samāsa-cakra leaf subtypes on the gold gallery

**Verdict: DEFER** — leaf-level accuracy 61 % at n = 18 is not unambiguous,
exactly as the handoff anticipated for a small gold. The probe is kept and
reusable; the one strong signal (confidence calibration, below) is recorded
as a lead, not an adoption.

## What ran

Choice probe over all 58 leaf subtypes of
`samasacakra/samasacakra-taxonomy.json` on the 18 gold gallery compounds.
Per compound one Jev `choice` question (`jev-1.13.0`, TypeSafe «System One»
API): state = compound + member glosses + context; criteria = the full
58-option map (58 ≤ 255 live limit). Gold = the taxonomy leaf whose
`diagram` field embeds that compound's example SVG — the curator's own
wiring, no relabelling by the probe.

- Script: [samasacakra/samasa_subtype_jev_choice_probe.py](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/samasa_subtype_jev_choice_probe.py)
  (dry-run default; `--run` live; ×3 retry).
- Raw results: [samasacakra/jev-subtype-choice-results.json](https://github.com/gasyoun/SamasaChakram/blob/main/samasacakra/jev-subtype-choice-results.json)
  (per-compound prediction, confidence, probabilities, usage, cost).
- Transport reused from Uprava `tools/jev_probe.py` (H5275) — no rebuild.

## Gold set definition (mechanical)

Every `klammerdiagramm-*.json` whose stem matches a taxonomy `diagram`
reference: 18 items over 17 distinct gold leaves
(`madhyamapadalopin` is gold twice — śāka-[priya]-pārthivaḥ and
abhijñāna-śākuntalam). Two documented exclusions: the superseded
uddāma plate render (same compound as the canonical D5 Leitan item — no
double counting) and yat-pādāmbhoja (no taxonomy leaf links it). The
handoff's «12-13» reflected the 16-07 gallery snapshot; the set has grown
since — all resolvable gold items were probed.

State design: deliberately leak-free — the JSON `desc` fields and the
gallery doc name the structure («a dvandva of dvandvas»), so the probe
states carry only member glosses, overall meaning and source/vigraha
context; no class or subtype term appears in any state.

## Results

| Metric | Value |
|---|---|
| Leaf-exact accuracy | **11/18 = 61.1 %** |
| Top-level class accuracy | 13/18 = 72.2 % |
| Mean cost per compound | $0.000191 (input $0.042/1M tok; run total $0.0034) |
| Mean confidence on hits | 0.81 (min 0.60) |
| Mean confidence on misses | 0.32 (max 0.56) |
| Gate conf ≥ 0.5 | answered 12/18, accuracy 11/12 |
| Gate conf ≥ 0.6 | answered 11/18, **accuracy 11/11** |

Per-subtype confusion (gold → predicted, n = 1 unless noted; `=` = hit):

```
adi = adi                       mayura = mayura
appositional = appositional     rupaka -> yatha
ekadesin = ekadesin             samahara-dv = samahara-dv
itaretara -> sasthi             samahare-dvigu = samahare-dvigu
loc-bv = loc-bv                 sasthi -> saptamyartha
madhyamapadalopin = (1) -> itaretara (1)     sasthyartha -> gen-bv
ubhayapada = ubhayapada         upamita -> loc-bv
upapada -> itaretara            uttarapade = uttarapade
yatha = yatha
```

The misses are informative, not random: `sasthi→saptamyartha` stays inside
the vibhakti-tatpuruṣa family (ṣaṣṭhī vs saptamī reading of the same
genitive-like relation); `sasthyartha→gen-bv` stays inside bahuvrīhi;
`upamita→loc-bv` and `rupaka→yatha` confuse the figurative subtypes of
karmadhāraya with neighbours. The model never invented an option outside
the 58.

## The one strong signal

Confidence separates hits from misses perfectly on this gold: every hit
has conf ≥ 0.60, every miss < 0.60 (gap 0.56 → 0.60). As a **gated**
classifier the probe is already usable behaviourally — answer when
confident, defer otherwise (61 % coverage at 100 % gate accuracy) — but
n = 18 makes the gate statistic fragile. Verdict stays DEFER; the
follow-up is gold growth, not threshold tuning.

## Reproduce

```bash
# dry-run (no network, validates all 18 requests):
python3 samasacakra/samasa_subtype_jev_choice_probe.py \
  --taxonomy samasacakra/samasacakra-taxonomy.json
# live (key in ~/.secrets/typesafe.env, TYPESAFE_API_KEY):
python3 samasacakra/samasa_subtype_jev_choice_probe.py \
  --taxonomy samasacakra/samasacakra-taxonomy.json --run \
  --out samasacakra/jev-subtype-choice-results.json
```

Requires the sibling `gasyoun/Uprava` clone (transport reuse,
`tools/jev_probe.py`, H5275). Offline selftest of the transport:
`python3 Uprava/tools/jev_probe.py --selftest` → 16/16 PASS (24-09-2026).

## Delivery (five fields)

- **Changed:** new probe script + results JSON + this note; nothing else
  in the repo touched.
- **Unchanged:** taxonomy, gallery, generator, wheel — all byte-identical.
- **Checks:** dry-run validates 18/18 requests; transport selftest 16/16
  PASS; live run 18/18 OK (2026-09-24).
- **Risks:** gold n = 18 over 58 options — accuracy CI is wide; the conf
  gate is one-sample-per-cell, fragile until gold grows; state glosses are
  worker-authored (plain lexical, leak-checked by construction).
- **Inspect:** the results JSON first, then the confusion table above.

_Provenance: probe subject jev-1.13.0 (TypeSafe System One API); harness
Uprava H5275; probe executed by OxAlpha (opencode/z-ai/glm-5.3-flash),
H5278, 24-09-2026._

_Гасунс_
