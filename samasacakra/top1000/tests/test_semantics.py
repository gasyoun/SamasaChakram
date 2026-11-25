class FakeProbe:
    def __init__(self, payload):
        self.payload = payload
        self.seen = None

    def ask(self, state, spec):
        self.seen = (state, spec)
        return self.payload


RULES = {
    "nodes": {
        "q_yesno": {"question": "Is it X?", "options": []},
        "q_choice": {"question": "Which subtype?", "options": [
            {"label": "A", "next": "r_tp"}, {"label": "B", "next": "r_bv"}]},
    }
}


def test_malformed_answer_becomes_unanswered():
    from semantics import answer_semantics
    out = answer_semantics("x", ["a", "b"], ["q_yesno"], [], RULES,
                           probe=FakeProbe({}), run=True)
    assert out == {}


def test_valid_yes_no_roundtrip():
    from semantics import answer_semantics
    out = answer_semantics("x", ["a", "b"], ["q_yesno"], [], RULES,
                           probe=FakeProbe({"q_yesno": {"choice": "yes"}}), run=True)
    assert out == {"q_yesno": True}


def test_option_choice_maps_to_next_id():
    from semantics import answer_semantics
    out = answer_semantics("x", ["a", "b"], ["q_choice"], [], RULES,
                           probe=FakeProbe({"q_choice": {"choice": "r_bv"}}), run=True)
    assert out == {"q_choice": "r_bv"}


def test_default_is_dry_run():
    from semantics import answer_semantics
    assert answer_semantics("x", ["a"], ["q_yesno"], [], RULES) == {}


def test_fewshot_examples_are_in_state():
    from semantics import answer_semantics
    probe = FakeProbe({})
    answer_semantics("x", ["a", "b"], ["q_yesno"],
                     [{"surface": "rājaputra", "vigraha": "rājñaḥ putraḥ", "coarse": "tatpurusa"}],
                     RULES, probe=probe, run=True)
    assert "rājaputra" in probe.seen[0]
