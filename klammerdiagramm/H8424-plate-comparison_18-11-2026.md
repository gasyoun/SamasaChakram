# H8424 historical plate comparison · 18-11-2026

The [committed printed plate](klammerdiagramm-target-plate.png) is the source —
MG-confirmed 19-11-2026 as **Leitan's original** (H8424). The
`klammerdiagramm-uddama-plate-historical.*` filenames are the legacy compatibility
output slot fixed by earlier commits; they do not attribute the source. It
was uploaded for [H814](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H814-Fable_claude-config_klammerdiagramm-1to1-plate-fix_12.07.26.md).
That brief identifies a reference image and calls for a visual side-by-side; it
does not identify editable artwork for the original. The current candidate is
an editable, opt-in SVG reconstruction. The original image is unmodified and is
not embedded in the SVG.

## Native comparison

| Measure | Old SVG browser replay | Current SVG browser replay |
|---|---:|---:|
| Dimensions | 1198 × 710 | 1213 × 723 |
| Pixels that differ from the source | 146,054 | 53,963 |
| Mean absolute channel error, 0–255 | 16.2143 | 0.8946 |
| Original geometry ink within one pixel of the remake | 16.18% | 99.97% |
| Original word-row ink within one pixel of the remake | 52.65% | 100.00% |
| Original caption and rule ink within one pixel of the remake | 21.38% | 99.88% |

The old SVG was rendered at its own native dimensions and placed at the source
origin without scaling. The current remake aligns at native scale; the figures
are **not** evidence of exact equality. The strict raster check still fails.
410 pixels differ by more than 64 channel values, down from 8,981 before this
lettering and linework calibration. The current word row has 9,144 dark pixels
at the 170 threshold; the source has 9,215.

The source hatches measure a horizontal period of 13.057 px and a shift of
−0.899 px per row, with a separate phase for band G. The captured SVG uses these
periods, the scan's elbow endpoints, a clipped outer arrow on A, measured
label cut-outs, and 103 individually measured horizontal dashes. Three
opacity layers calibrate the diagonal strokes to the scan's edge coverage.

The reference carries RGB subpixel fringes in its lettering. The lettering
asset preserves those using independently traced closed contours in each
color plane, with three fitted coverages per plane. The displayed shapes are
editable SVG paths; the Sanskrit, captions and labels are also present as
text. The trace derives only the lettering from the reference. Hatches,
arrowheads, elbows, bands, and rules are drawn from the plate parameters.

## Reproduce the checks

Run from the repository root. The SVG/HTML builder uses the existing Charis
subset and fontTools. The comparison uses Pillow, NumPy, SciPy and Playwright.
Use a pinned Chromium build when comparing results across versions.

```sh
python3 klammerdiagramm/trace_historical_plate_lettering.py \
  klammerdiagramm/klammerdiagramm-target-plate.png \
  klammerdiagramm/klammerdiagramm-uddama-plate-lettering.json
python3 klammerdiagramm/build_klammerdiagramm.py \
  --config klammerdiagramm/klammerdiagramm-uddama-plate-historical.json \
  --out klammerdiagramm/klammerdiagramm-uddama-plate-historical
python3 klammerdiagramm/check_historical_plate.py
python3 scripts/check_example_pack.py
python3 klammerdiagramm/compare_historical_plate.py \
  klammerdiagramm/klammerdiagramm-target-plate.png \
  klammerdiagramm/klammerdiagramm-uddama-plate-historical.html /tmp/h8424-comparison
python3 klammerdiagramm/check_historical_plate.py --exact-png
```

The comparison saves the native export as `browser.png`, and a triptych of
source, remake and overlay as `original-remake-overlay.png`. Shared ink is
dark; red marks original-only ink and blue marks remake-only ink. The geometry
census passes the current candidate and rejects the old SVG at baseline
`e251e09ec1287f82fa5f60b6a3f40b5a99460cb3`. The teaching-pack check passes.

The [SHA-256 manifest](h8424-other-examples-sha256.tsv) records the 19 other
explicit configs and the no-config default. Their fresh SVG, HTML and PNG
renders match baseline replays under the same browser, and their tracked assets
are unchanged. The archived PNG encoding is not reproduced by this browser
capture even on the baseline; those archive hashes are recorded separately.

## Re-verified 19-11-2026 (GLM 5.3, H8455)

Fresh reproduction from a clean temp folder (lettering trace → build) is
**byte-identical** to the committed draft for both the SVG
(SHA-256 `44684fdf1c46a342088bfa0af13dca3fb83ebd23137e8f3c7916ba088c9220e7`)
and the font-embedded HTML
(SHA-256 `a4a64853c7abb69b4b69bac960bf09ef0a2cb13f158fcff35b0ea888a4a07976`);
the regenerated lettering JSON is also byte-stable. The geometry census passes
the current candidate and **fails the baseline SVG** extracted from
`e251e09ec1287f82fa5f60b6a3f40b5a99460cb3` (missing lettering contours, band
and rung mismatches). `scripts/check_example_pack.py` passes (0 hard failures).

Browser note: Playwright's pinned Chromium is not installed on this box; the
replay used headless Google Chrome (`--browser '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'`),
offline `file://` navigation only. Chrome-measured fresh figures agree with the
table above at rounding precision (geometry ink within 1 px ≈ 99.97% recall /
99.93% precision; text 100.00%; 410+ channel-error pixels persist). The strict
`--exact-png` raster check still fails — that residual stands and the figures
above are not evidence of exact equality. The comparison accepts a standalone
SVG, SVG in HTML, or a PNG, so both rejected PNGs and the new SVG can be checked
directly against the same source. The fresh HTML raster also matches the
committed reconstruction PNG byte for byte on this Chrome build.

Residual not fixed here: `teaching-pack/EXAMPLE_PACK.md` still carries the
stale "plate signed off 15-07-2026 (1:1)" wording; the H8455 execution brief
freezes the teaching pack, so that correction is left to the publishing pass.
