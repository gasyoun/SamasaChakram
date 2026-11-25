def test_extract_known_labels_and_ambiguous():
    from scharf import extract_scharf, coarse_of
    text = ("rājaputraḥ — ṣaṣṭhī-tatpuruṣa\n"
            "śītoṣṇam — karmadhāraya\n"
            "rāmakṛṣṇau — dvandva\n"
            "vidyādhanaḥ — ambiguous (tatpuruṣa / bahuvrīhi)\n")
    rows = extract_scharf(text)
    assert [(r["compound"], r["coarse"], r["ambiguous"]) for r in rows] == [
        ("rājaputraḥ", "tatpurusa", False),
        ("śītoṣṇam", "karmadharaya", False),
        ("rāmakṛṣṇau", "dvandva", False),
        ("vidyādhanaḥ", "unknown", True),
    ]
    assert coarse_of("ṣaṣṭhī-tatpuruṣa") == "tatpurusa"
