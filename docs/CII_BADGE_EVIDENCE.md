# OpenSSF Best Practices badge — evidence worksheet (Passing tier)

_Created 25-11-2026. Companion to the Scorecard hardening change in PR #45._

The badge itself must be created by a human at <https://www.bestpractices.dev/>
(sign in with GitHub → "Add a project" → `https://github.com/gasyoun/SamasaChakram`).
This worksheet supplies the justifications and URLs so the form can be filled
without re-deriving the evidence. Criterion IDs match
<https://www.bestpractices.dev/en/criteria/0>.

URLs below are relative to `https://github.com/gasyoun/SamasaChakram/blob/main/`
unless stated otherwise.

## Basics — documented

| ID | Status | Evidence / justification |
|---|---|---|
| `description_good` | Met | `README.md` → «Что это» — states what the wheel solves. |
| `interact` | Met | `README.md` (obtain / quick start), `CONTRIBUTING.md` (contribute), [Issues](https://github.com/gasyoun/SamasaChakram/issues) (feedback). |
| `contribution` | Met | `CONTRIBUTING.md` → "Contribution process" (branch off `main`, PR, required checks, protected `main`). |
| `contribution_requirements` | Met | `CONTRIBUTING.md` → "Requirements for acceptable contributions" (tests, changelog queue, pinned actions, no binaries, style). |
| `floss_license`, `floss_license_osi`, `license_location` | Met | `LICENSE` at repo root — Apache License 2.0 (OSI approved; Scorecard License = 10). |
| `documentation_basics` | Met | `README.md` + `docs/` rendered pages. |
| `documentation_interface` | Met | `README.md` → «Быстрый старт для разработчика» lists generator entry points; `docs/index.html` is the public interface. |
| `sites_https` | Met | GitHub repository and `gasyoun.github.io` Pages both HTTPS. |
| `discussion` | Met | GitHub Issues — searchable, per-issue URLs, open to new participants, no proprietary client. |
| `english` | Met | `CONTRIBUTING.md` and `SECURITY.md` are in English; English issues are accepted. |
| `maintained` | Met | Scorecard Maintained = 10 (23 commits in the last 90 days). |

## Change control — documented

| ID | Status | Evidence / justification |
|---|---|---|
| `repo_public`, `repo_track`, `repo_interim`, `repo_distributed` | Met | Public git repository, `[0.7.4]`-era history, intermediate commits on branches and PRs. |
| `version_unique`, `version_semver`, `version_tags` | Met | `CHANGELOG.md` release headings and git tags `v0.1.0` … `v0.7.4` (SemVer). |
| `release_notes` | Met | `CHANGELOG.md` — human-written, dated `DD-MM-YYYY`, release sections; not a raw `git log`. |
| `release_notes_vulns` | N/A | No publicly known runtime vulnerability has been fixed in a release. |

## Reporting

| ID | Status | Evidence / justification |
|---|---|---|
| `report_process`, `report_tracker`, `report_archive` | Met | [GitHub Issues](https://github.com/gasyoun/SamasaChakram/issues) — public, searchable archive. |
| `report_responses`, `enhancement_responses` | **Human check** | Confirm a majority of issues in the last 2–12 months received a response; link the issue list in the justification. |
| `vulnerability_report_process` | Met | `SECURITY.md` — private reporting process. |
| `vulnerability_report_private` | Met | `SECURITY.md` — private email `gasyoun@gmail.com`, no public issue. |
| `vulnerability_report_response` | N/A | No vulnerability reports received in the last 6 months. |

## Quality

| ID | Status | Evidence / justification |
|---|---|---|
| `build` | Met | Python generators (`samasacakra/build_samasacakra.py`, `build_pilot.py`, `klammerdiagramm/build_klammerdiagramm.py`) rebuild all published artifacts from source. |
| `test`, `test_invocation`, `test_continuous_integration` | Met | 27 tests under `samasacakra/top1000/tests/`; `python -m pytest samasacakra/top1000/tests -q`; `.github/workflows/pytest.yml` on every PR and push to `main`. |
| `test_policy`, `tests_are_added`, `tests_documented_added` | Met | `CONTRIBUTING.md` makes tests mandatory for new behaviour; recent changes ship with tests in `tests/`. |
| `warnings`, `warnings_fixed`, `warnings_strict` | **Gap** | No linter wired yet. Cheapest fix: add `ruff check` as a pinned CI step once the current tree is clean. |

## Security

| ID | Status | Evidence / justification |
|---|---|---|
| `know_secure_design`, `know_common_errors` | **Human check** | MG to attest; link the estate security policy / training record if one exists. |
| `crypto_*` (8 criteria) | N/A | The project produces documentation and reading aids; it implements no cryptography. |
| `delivery_mitm`, `delivery_unsigned` | Met | HTTPS/SSH delivery only; all third-party Actions pinned to full SHA; no hash fetched over HTTP. |
| `vulnerabilities_fixed_60_days`, `vulnerabilities_critical_fixed` | Met | Scorecard Vulnerabilities = 10 (0 open known vulnerabilities); Dependabot enabled. |
| `no_leaked_credentials` | **Human check** | Run a secret scan over the public history before attesting (no credential is intentionally tracked; `.agent_policy.json` blocks committing `.env`). |
| `static_analysis`, `static_analysis_common_vulnerabilities`, `static_analysis_fixed`, `static_analysis_often` | Met | `.github/workflows/codeql.yml` — Python CodeQL on every push, PR and weekly; SARIF uploaded to code scanning. |
| `dynamic_analysis*` | N/A | Python documentation/reading-aid code, no memory-unsafe language; dynamic analysis is only a SHOULD for this project. |

## Remaining human steps

1. Sign in at <https://www.bestpractices.dev/> with the `gasyoun` GitHub account
   and add `https://github.com/gasyoun/SamasaChakram`.
2. Fill the form from the tables above; the "Human check" rows need your own
   attestation, and the `warnings` gap needs a linter step before it can be Met.
3. Once the badge URL exists, add the badge image to `README.md` — that is what
   moves Scorecard's CII-Best-Practices from 0 to 2 (in progress) / 5 (passing).
