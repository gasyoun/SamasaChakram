# Contributing to SamasaChakram

_English document; bug reports and comments in English are welcome. Краткая
русская версия — в конце файла._

## What this project is

SamasaChakram is a Sanskrit poetics / reading aid: an interactive wheel of
samāsa classes, Klammerdiagramm plates, lesson packs and the supporting
`samasacakra/top1000` corpus pipeline. The [README](README.md) describes the
problem it solves; the [repository map](README.md#карта-репозитория) shows where
each part lives.

## Getting the software

```bash
git clone https://github.com/gasyoun/SamasaChakram.git
cd SamasaChakram
```

Rendered pages are published at
[gasyoun.github.io/SamasaChakram](https://gasyoun.github.io/SamasaChakram/).
Python 3.11+, `python-docx` and `indic-transliteration` are needed for the
generators; the generators are listed in the README's developer quick start.

## Feedback and bug reports

- Use [GitHub Issues](https://github.com/gasyoun/SamasaChakram/issues) for bug
  reports and enhancement requests. Please include the commit or release, a
  minimal reproduction and the observed vs expected result.
- Report security problems **privately** as described in [SECURITY.md](SECURITY.md)
  — do not open a public issue for a vulnerability.
- Issue history is public and searchable; English reports are accepted.

## Contribution process

1. Branch off `main` (or fork the repository).
2. Make the change in a focused commits; keep generated artifacts reproducible
   by re-running the generator rather than hand-editing output.
3. Open a pull request against `main`. Every PR runs these required checks:
   - **Run Python tests** — `python -m pytest samasacakra/top1000/tests -q`
   - **Analyze (python)** — CodeQL static analysis
   - **Changelog — no duplicated entries** and
     **Changelog — released headings are append-only**
4. `main` is protected: no force pushes or deletion, a review is required before
   merge, and at least one status check must pass. Dependabot updates are
   auto-merged by `.github/workflows/dependabot-auto-merge.yml` after checks.

## Requirements for acceptable contributions

- **Tests.** Add or update tests under `samasacakra/top1000/tests/` for new or
  changed behaviour. The suite must pass locally before the PR is opened.
- **Changelog.** Add one bullet file under `changelog_queue/` named
  `YYYY-MM-DD-HHMMSS-<slug>.md`; it is consumed at release cut. Do not edit the
  released sections of `CHANGELOG.md` directly.
- **Actions.** Pin every third-party GitHub Action to a full commit SHA and keep
  workflow top-level tokens read-only (writes only at job level). This is
  enforced by the OpenSSF Scorecard workflow.
- **No binaries.** Do not commit generated executables or compiled artifacts;
  rebuild them from source. Generated docs and SVG plates are fine.
- **Style.** Follow `.editorconfig` (UTF-8, LF, trailing newline). Keep the
  existing Russian/IAST/Devanagari conventions; do not mix transliteration with
  Devanagari inside one card line.
- **Licence.** Contributions are licensed under [Apache-2.0](LICENSE).

## Русская версия

Изменения присылаются pull request в `main`: ветка от `main`, фокус на одной
задаче, обязательные проверки — тесты pytest, CodeQL и две проверки CHANGELOG.
`main` защищён: без force-push и удаления, перед слиянием нужны ревью и зелёные
проверки. Для каждого изменения добавьте один файл-заметку в `changelog_queue/`
и тест в `samasacakra/top1000/tests/`. Сторонние GitHub Actions пиннятся по
полному SHA, токены workflow на верхнем уровне только read-only. Бинарники в
репозиторий не кладутся. Ошибки и улучшения — в
[Issues](https://github.com/gasyoun/SamasaChakram/issues); уязвимости — приватно
по [SECURITY.md](SECURITY.md).
