import hashlib
import json


def test_killgate_blocks_publication():
    from evaluate import gate
    assert gate({"coarse_accuracy": 0.69})["publish"] is False
    result = gate({"coarse_accuracy": 0.70})
    assert result["publish"] is True and result["threshold"] == 0.70


def test_evaluate_counts_unknown_as_uncovered():
    from evaluate import evaluate
    metrics = evaluate(
        [{"type": "tatpurusa"}, {"type": "unknown"}, {"type": "dvandva"}],
        [{"coarse": "tatpurusa"}, {"coarse": "bahuvrihi"}, {"coarse": "dvandva"}],
    )
    assert metrics["coverage"] == 2 / 3
    assert metrics["coarse_accuracy"] == 1.0
    assert round(metrics["unknown_rate"], 3) == 0.333


def test_rank_from_wordfreq_transliterates_iast(tmp_path):
    from build_top1000 import rank_from_wordfreq
    cmps = tmp_path / "cmps.csv"
    freq = tmp_path / "wf.txt"
    cmps.write_text("tad;tad tad\nrājaputra;rājan putra\nrāmalakṣmaṇau;rāma lakṣmaṇa\n", encoding="utf-8")
    freq.write_text("tad 999\nrAjaputra 37\nrAmalakzmaRO 5\n", encoding="utf-8-sig")
    rows = rank_from_wordfreq(cmps, freq, cap=10)
    assert [r["compound"] for r in rows] == ["rājaputra", "rāmalakṣmaṇau"]
    assert [r["freq"] for r in rows] == [37, 5]


def test_combine_rankings_dedupes_and_marks_basis():
    from build_top1000 import combine_rankings
    measured = [{"compound": "a", "members": ["a", "b"], "freq": 5}]
    proxy = [{"compound": "a", "members": ["a", "b"], "freq": 1, "basis": "lemma_proxy"},
             {"compound": "b", "members": ["c", "d"], "freq": 1, "basis": "lemma_proxy"}]
    out = combine_rankings(measured, proxy, cap=2)
    assert [r["compound"] for r in out] == ["a", "b"]
    assert [r["rank"] for r in out] == [1, 2]
    assert out[0]["basis"] == "measured" and out[1]["basis"] == "lemma_proxy"


def test_fail_closed_artifact_check(tmp_path):
    from check_top1000 import check
    rows = "\t".join(["rank", "compound", "members", "freq", "type_coarse", "type_fine",
                      "confidence", "decision_path", "source", "gold_agree", "license"])
    body = "\t".join(["1", "x", "a b", "7", "tatpurusa", "TP", "", "", "drumam+jev", "", "CC BY 4.0"])
    tsv = tmp_path / "top1000_typed.tsv"
    tsv.write_text(rows + "\n" + body + "\n", encoding="utf-8")
    manifest = {"sha256": hashlib.sha256(tsv.read_bytes()).hexdigest(),
                "threshold": 0.70, "publish": True}
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(manifest), encoding="utf-8")
    assert check(tsv, mf, expected_rows=1) is True
    body2 = body.replace("tatpurusa", "unknown")
    tsv.write_text(rows + "\n" + body2 + "\n", encoding="utf-8")
    assert check(tsv, mf, expected_rows=1) is False
