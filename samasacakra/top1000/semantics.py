import sys
from pathlib import Path


def load_probe():
    uprava = Path(__file__).resolve().parents[3] / "Uprava" / "tools"
    sys.path.insert(0, str(uprava))
    import jev_probe
    return jev_probe


def build_spec(questions, rules):
    spec = {}
    for q in questions:
        node = rules["nodes"][q]
        options = node.get("options") or []
        criteria = ({o["next"]: o["label"] for o in options} if options
                    else {"yes": "answer yes", "no": "answer no"})
        spec[q] = {"type": "choice", "question": node["question"], "criteria": criteria}
    return spec


def parse_answers(raw, questions, rules):
    out = {}
    for q in questions:
        value = raw.get(q) if isinstance(raw, dict) else None
        choice = value.get("choice") if isinstance(value, dict) else None
        options = rules["nodes"][q].get("options") or []
        valid = {o["next"] for o in options} if options else {"yes", "no"}
        if choice not in valid:
            continue
        out[q] = choice if options else (choice == "yes")
    return out


def answer_semantics(surface, members, questions, fewshot, rules,
                     run=False, max_cost=0.0, probe=None):
    if not run or not questions:
        return {}
    spec = build_spec(questions, rules)
    state = {"compound": surface, "members": members,
             "few_shot": [{"surface": g.get("surface", ""),
                           "vigraha": g.get("vigraha", ""),
                           "type": g.get("coarse", "")} for g in fewshot[:8]],
             "questions": {q: spec[q]["question"] for q in questions}}
    if probe is not None:
        return parse_answers(probe.ask(state, spec), questions, rules)
    return _live(load_probe(), state, spec, questions, rules, max_cost)


def _live(p, state, spec, questions, rules, max_cost):
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
    return parse_answers(body.get("answers", {}), questions, rules)
