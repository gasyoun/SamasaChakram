"""Tests for the base-productivity builder (H8607).

The real inputs (cmps.csv, compounds.txt) are external and never committed, so the tests
use small synthetic fixtures that mirror their exact on-disk shapes.
"""

import json
from pathlib import Path

TAXONOMY = Path(__file__).resolve().parents[2] / "samasacakra-taxonomy.json"


def test_fold_preserves_vowel_length_and_folds_nasals():
    from build_base_productivity import fold

    assert fold("pūrva") != fold("purva")          # length is meaning-bearing
    assert fold("saṃskṛta") == fold("sanskṛta")    # anusvāra folds to n
    assert fold("aṅguli") == fold("aṃguli")        # homorganic nasal folds to n
    assert fold("rājaputraḥ") == fold("rājaputra")  # final visarga stripped
    assert fold("rasaṃ") == fold("rasam")          # word-final anusvāra is /m/


def test_fold_compound_drops_sandhi_marker():
    from build_base_productivity import fold_compound

    assert fold_compound("prā@pto@daka") == fold_compound("prāptodaka")


def test_derivation_covers_every_leaf():
    from build_base_productivity import DERIVATION

    data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    keys = {
        f"{cls['id']}/{fam['id']}/{leaf['id']}"
        for cls in data["classes"]
        for fam in cls.get("families", [])
        for leaf in fam.get("leaves", [])
    }
    assert len(keys) == 58
    assert keys <= set(DERIVATION)
    for purva, uttara, basis in DERIVATION.values():
        assert purva and uttara
        assert basis in {"ex", "vigraha", "both"}


def test_build_counts_both_sources_and_marks_examples(tmp_path):
    from build_base_productivity import build

    cmps = tmp_path / "cmps.csv"
    cmps.write_text(
        "pūrvakāya; pūrva kāya\n"
        "pūrvajanma; pūrva janman\n"
        "sujanma; su janman\n",
        encoding="utf-8",
    )
    compounds = tmp_path / "compounds.txt"
    compounds.write_text(
        "2:pūrva:+kāya prā@pto\n"
        "1:kāya:+pūrva\n",
        encoding="utf-8",
    )

    summary, rows = build(cmps, compounds)

    purva_rows = [r for r in rows if r["base"] == "pūrva" and r["role"] == "pūrvapada"]
    compounds_seen = {r["compound"] for r in purva_rows}
    assert {"pūrvakāya", "pūrvajanma", "prāpto"} <= compounds_seen
    # the count is the group size, and it is stable on every row of the group
    assert {r["count"] for r in purva_rows} == {len(purva_rows)}

    example_row = next(r for r in purva_rows if r["compound"] == "pūrvakāya")
    assert example_row["already_in_our_examples"] == "да"
    assert example_row["type_label"] == ""       # no verified tag -> empty column

    assert len(summary) == 58                    # one summary row per leaf


def test_build_is_deterministic(tmp_path):
    from build_base_productivity import build

    cmps = tmp_path / "cmps.csv"
    cmps.write_text("rājaputra; rājan putra\nrājarṣi; rājan ṛṣi\n", encoding="utf-8")
    compounds = tmp_path / "compounds.txt"
    compounds.write_text("1:rājan:+putra\n", encoding="utf-8")

    first = build(cmps, compounds)
    second = build(cmps, compounds)
    assert first == second
