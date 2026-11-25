RULES = {
    "nodes": {
        "start": {"id": "start", "yes": "check", "no": "r_bv", "kind": "form", "options": []},
        "check": {"id": "check", "yes": "r_tp", "no": "r_bv", "kind": "semantic", "options": []},
        "choice": {"id": "choice", "yes": "", "no": "", "kind": "semantic",
                   "options": [{"label": "A", "next": "r_tp"}, {"label": "B", "next": "r_bv"}]},
    },
    "results": {"r_bv": {"type": "bahuvrihi", "fine": "BV"},
                "r_tp": {"type": "tatpurusa", "fine": "TP"}},
    "avyaya_words": ["upa"], "preverbs": ["prati"], "numerals": ["eka", "dvi"],
}


def test_form_branch_and_unanswered_semantic_node():
    from classify import classify
    r = classify("upagaṅgam", ["upa", "gaṅgā"], {}, RULES)
    assert r["type"] == "unknown"
    assert r["path"] == ["start", "check"]
    assert r["unanswered"] == ["check"]


def test_semantic_answer_reaches_result():
    from classify import classify
    r = classify("upaputraḥ", ["upa", "putra"], {"check": True}, RULES)
    assert r["type"] == "tatpurusa" and r["unanswered"] == []


def test_option_node_resolves_by_next_id():
    from classify import classify
    rules = dict(RULES)
    rules["nodes"] = dict(RULES["nodes"])
    rules["nodes"]["start"] = dict(RULES["nodes"]["choice"])
    r = classify("x", ["a", "b"], {"start": "r_bv"}, rules)
    assert r["type"] == "bahuvrihi" and r["fine"] == "BV"
    assert r["unanswered"] == []


def test_unknown_option_choice_stays_unanswered():
    from classify import classify
    rules = dict(RULES)
    rules["nodes"] = dict(RULES["nodes"])
    rules["nodes"]["start"] = dict(RULES["nodes"]["choice"])
    r = classify("x", ["a", "b"], {"start": "r_missing"}, rules)
    assert r["type"] == "unknown" and r["unanswered"] == ["start"]
