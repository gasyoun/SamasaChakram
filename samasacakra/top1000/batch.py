import sys
from pathlib import Path

from classify import classify
from semantics import load_probe, parse_answers


def build_batch(items, rules, fewshot):
    """items: list of dicts with `surface` and `members`. Returns (state, spec, qids)."""
    qids = [nid for nid, node in rules["nodes"].items() if node["kind"] == "semantic"]
    spec, state_lines = {}, []
    shot = [f'{g.get("surface", "")}: {g.get("vigraha", "")} → {g.get("coarse", "")}'
            for g in fewshot[:8]]
    state_lines.append("Gold examples (compound: vigraha → type):")
    state_lines.extend(shot)
    for i, item in enumerate(items):
        state_lines.append(
            f'[{i}] Compound: {item["surface"]} (members: {", ".join(item["members"])})')
    for i in range(len(items)):
        for q in qids:
            node = rules["nodes"][q]
            options = node.get("options") or []
            criteria = ({o["next"]: o["label"] for o in options} if options
                        else {"yes": "answer yes", "no": "answer no"})
            spec[f"{i}__{q}"] = {"type": "choice", "question":
                                 f"For compound [{i}] ({items[i]['surface']}): {node['question']}",
                                 "criteria": criteria}
    return "\n".join(state_lines), spec, qids


def classify_batch(items, rules, fewshot, run=False, max_cost=0.0, probe=None):
    if not items:
        return []
    state, spec, qids = build_batch(items, rules, fewshot)
    if not run:
        return [classify(it["surface"], it["members"], {}, rules) for it in items]
    if probe is not None:
        raw = probe.ask(state, spec)
    else:
        raw = _live(state, spec, max_cost)
    results = []
    for i, item in enumerate(items):
        answers = {}
        for q in qids:
            val = parse_answers({q: raw.get(f"{i}__{q}")}, [q], rules).get(q)
            if val is not None:
                answers[q] = val
        results.append(classify(item["surface"], item["members"], answers, rules))
    return results


def _live(state, spec, max_cost):
    p = load_probe()
    req = {"state": state, "model": p.DEFAULT_MODEL, "questions": spec}
    ok, why = p.validate_request(req)
    if not ok:
        raise ValueError(why)
    api_key, model, endpoint = p.resolve_config(
        type("A", (), {"env_file": str(p.DEFAULT_ENV_FILE)})())
    if not api_key:
        raise RuntimeError("TYPESAFE_API_KEY not found")
    req["model"] = model
    status, body = p.call_jev(req, api_key, endpoint, timeout_s=p.REQUEST_TIMEOUT_S)
    if p.classify_result(status, body) != "OK":
        return {}
    cost = p.cost_usd(body.get("usage"))
    if cost is not None and cost > max_cost:
        raise RuntimeError("cost cap exceeded")
    return body.get("answers", {})


def batched(seq, size=10):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]
