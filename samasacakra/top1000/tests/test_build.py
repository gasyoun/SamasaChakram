def test_rank_uses_measured_frequency_and_drops_missing(tmp_path):
    cmps = tmp_path / "cmps.csv"
    names = tmp_path / "names.csv"
    cmps.write_text("rājaputra;rājan putra\nghost;ghost word\n", encoding="utf-8")
    names.write_text("rājaputra;x;y;37\nghost;x;y;0\n", encoding="utf-8")
    from build_top1000 import rank_compounds
    rows = rank_compounds(cmps, names, cap=10)
    assert [r["compound"] for r in rows] == ["rājaputra"]
    assert rows[0]["members"] == ["rājan", "putra"]
    assert rows[0]["freq"] == 37


def test_cap_is_applied(tmp_path):
    cmps = tmp_path / "c.csv"
    names = tmp_path / "n.csv"
    cmps.write_text("".join(f"w{i};a b\n" for i in range(5)), encoding="utf-8")
    names.write_text("".join(f"w{i};x;y;{5-i}\n" for i in range(5)), encoding="utf-8")
    from build_top1000 import rank_compounds
    assert [r["rank"] for r in rank_compounds(cmps, names, cap=2)] == [1, 2]
