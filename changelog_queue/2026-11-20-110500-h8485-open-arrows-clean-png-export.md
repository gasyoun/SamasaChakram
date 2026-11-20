- **H8485 — open-arrow member mode + clean PNG export (gallery repair).**
  `klammerdiagramm/build_klammerdiagramm.py`: every real visible member now
  carries ONE open (unfilled) arrow aligned to its centre, tail joined by a
  single stem into its hatched bar — replacing the legacy pair of filled
  edge arrows and their two border stems; ghost members stay arrow-free
  (D4 canary intact). I/II часть captions are placed by measured zone
  width: inline (legacy geometry byte-preserved) wherever they fit, raised
  to their own aligned row above when a narrow part-split leaves no room —
  the śīta-uṣṇa-sukha-duḥkha-dāḥ and janma-roga-maraṇa-ādiḥ caption/ogee
  collisions are fixed. All 19 non-plate SVG/HTML/PNG triples regenerated.
- `klammerdiagramm/export_png.py` — reusable clean PNG export: ONE
  persistent offline Chrome context (system executable, light scheme, 1×
  scale, every non-file/data request blocked), screenshot cropped exactly
  to the SVG element bounds (no browser chrome, no page padding, native
  viewBox dimensions).
- `scripts/check_h8485_gallery.py` — mechanical acceptance gate: 19
  triples inventoried, one-open-arrow-per-real-member, ghosts free of
  arrows/stems, caption placement rules, native-size clean-margin PNGs,
  and the frozen Leitan plate side (source scan PNG + historical
  config/lettering/SVG/HTML/PNG) sha256-pinned byte-identical.
- `teaching-pack`: pañca-gava-dhanaḥ category corrected to
  "dvigu (karmadhāraya subtype) inside bahuvrīhi — D1" (was wrongly
  "inside tatpuruṣa"; own vigraha pañca gāvo dhanaṃ yasya saḥ), recorded
  as correction R3; `EXAMPLE_PACK.md` regenerated. Graph and lesson
  decisions unchanged.
