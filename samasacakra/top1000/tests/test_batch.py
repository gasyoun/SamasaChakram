RULES = {
    "nodes": {
        "start": {"question": "Q?", "kind": "semantic", "options": [],
                  "yes": "r_tp", "no": "r_bv"},
    },
    "results": {"r_tp": {"type": "tatpurusa", "fine": "TP"},
                "r_bv": {"type": "bahuvrihi", "fine": "BV"}},
}


class FakeProbe:
    def __init__(self, payload):
        self.payload = payload
        self.seen = None

    def ask(self, state, spec):
        self.seen = (state, spec)
        return self.payload


def test_batch_answers_are_scoped_per_compound():
    from batch import classify_batch
    items = [{"surface": "a", "members": ["x", "y"]},
             {"surface": "b", "members": ["p", "q"]}]
    probe = FakeProbe({"0__start": {"choice": "yes"}, "1__start": {"choice": "no"}})
    out = classify_batch(items, RULES, [], run=True, probe=probe)
    assert [r["type"] for r in out] == ["tatpurusa", "bahuvrihi"]
    assert len(probe.seen[1]) == 2


def test_batch_dry_run_returns_unknown():
    from batch import classify_batch
    out = classify_batch([{"surface": "a", "members": ["x", "y"]}], RULES, [])
    assert out[0]["type"] == "unknown"


def test_batched_splits_evenly():
    from batch import batched
    assert [len(c) for c in batched(list(range(23)), 10)] == [10, 10, 3]
