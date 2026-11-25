def test_h989_uses_pass_a_and_keeps_vigraha(tmp_path):
    d = tmp_path / "tatpurusha" / "data"
    d.mkdir(parents=True)
    (d / "validation_sample.tsv").write_text(
        "cpd_token_id\tcompound_surface\n1\trājaputra\n", encoding="utf-8")
    (d / "annotations_full.tsv").write_text(
        "pass\tcpd_token_id\tcoarse\tfine\tvigraha\trationale\n"
        "A\t1\ttatpurusa\tsasthi\trājñaḥ putraḥ\tx\n"
        "B\t1\ttatpurusa\tsasthi\trājñaḥ putraḥ\tx\n", encoding="utf-8")
    from gold import load_h989
    assert load_h989(tmp_path) == [{
        "id": "1", "surface": "rājaputra", "coarse": "tatpurusa",
        "fine": "sasthi", "vigraha": "rājñaḥ putraḥ"}]


def test_gita_excludes_dual_tags(tmp_path):
    p = tmp_path / "g.tsv"
    row = lambda form, tag: "\t".join(["1.01", "1", form] + [""] * 11 + [tag, ""])
    header = ["verse", "widx", "form", "lemma", "root", "pos", "case", "number", "gender",
              "person", "tense", "voice", "nonfinite", "derivation", "compound", "raw_morph"]
    p.write_text("\t".join(header) + "\n" + row("a", "tatpurusa") + "\n" + row("b", "DV/TP") + "\n",
                 encoding="utf-8")
    from gold import load_gita
    assert [r["coarse"] for r in load_gita(p)] == ["tatpurusa"]


def test_fewshot_split_is_seeded():
    from gold import split_fewshot
    gold = [{"id": str(i)} for i in range(120)]
    a, b = split_fewshot(gold, n=60, seed=20260715)
    a2, b2 = split_fewshot(gold, n=60, seed=20260715)
    assert (a, b) == (a2, b2)
    assert len(a) == 60 and len(b) == 60 and not ({x["id"] for x in a} & {x["id"] for x in b})
