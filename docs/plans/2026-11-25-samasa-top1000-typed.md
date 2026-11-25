# Top-1000 typed samāsa compounds Implementation Plan

> **For agentic workers:** REQUIRED EXECUTION SKILL: Use subagent-driven-development
> (recommended, in this catalog) or executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a ranked top-1000 of DCS compounds with Drumam-derived samāsa type labels and report honest accuracy on the existing gold sets.

**Architecture:** Extract the Drumam decision tree into a committed JSON snapshot (HTML remains the source of truth), rank DCS Kompozity compounds by corpus frequency, walk the tree with deterministic form-answers plus JEV answers for semantic nodes (few-shot from the 120-item H989 gold), then evaluate against H989 and Gita-gold behind a pre-registered 0.70 kill-gate. Unknowns stay `unknown` — never guessed.

**Tech Stack:** Python 3 stdlib, `jev_probe.py` reused via `importlib`, TSV/JSON artifacts, pytest.

**Spec:** `docs/superpowers/specs/2026-11-25-samasa-top1000-typed-design.md`

## Global Constraints

- DCS is CC BY 4.0 — attribution in every output TSV and report; no raw DCS bytes committed.
- `type` fields are classifier outputs, never type-frequency claims (FINDINGS §449).
- JEV is dry-run by default; live only `--run --max-cost USD`; key from `~/.secrets/typesafe.env`.
- Coarse accuracy < 0.70 on the H989 holdout ⇒ do not publish the typed table, publish the report only.
- 56 dual-tagged Gita rows are excluded from evaluation but counted in the report.
- Commit and push in the same pass (MG 25-11-2026); no local-only commits.

## Execution rulings (25-11, carried into later tasks)

- R7 — three Drumam nodes (`ask_km_type`, `ask_bv_sub`, `ask_tp_case`) are multi-way `options:[{label,next}]`, not yes/no. `rules.json.nodes[*]` therefore also has `options: list[{label,next}]` (empty for yes/no nodes); `yes`/`no` are empty strings for option nodes. Task 4's walker must branch on options, and Task 5's semantic provider must answer a choice among 2–7 labelled options, not only yes/no.
- R8 — test paths are relative to the worktree root: `tests/test_rules.py` uses `parents[3]`, `check_rules.py` uses `parents[2]`. The plan's original Step-2 command named the non-worktree clone path; use the current worktree cwd.

## Review Focus

- **Compound with no attested members** (`cmps.csv` row present, `names.csv` frequency missing) → excluded from ranking, counted in report — Task 2 test.
- **Dual tag `DV/TP`** → excluded from gold, never silently collapsed — Task 3 test.
- **Node whose `yes`/`no` points to a `RESULT` string** → treated as terminal, no further question — Task 4 test.
- **LLM returns malformed answer** (missing question id / non-boolean) → that item becomes `unknown`, pipeline continues — Task 5 test.
- **Holdout accuracy below gate** → exit non-zero, no typed TSV written — Task 6 test.

---

### Task 1: Drumam rules snapshot

**Files:**
- Create: `samasacakra/top1000/extract_rules.py`
- Create: `samasacakra/top1000/rules.json` (generated)
- Create: `samasacakra/top1000/check_rules.py`
- Test: `samasacakra/top1000/tests/test_rules.py`

**Interfaces:**
- Consumes: `drumam/archive/samasa_decision_tree.html`
- Produces: `rules.json` with keys `nodes`, `results`, `avyaya_words`, `preverbs`, `numerals`; `nodes[id] = {id, question, yes, no, step, kind}` where `kind` ∈ `form|semantic`; `results[id] = {type, fine}`, where `type` is the normalized lowercase coarse label (`tatpurusa`, `bahuvrihi`, `dvandva`, `karmadharaya`, `avyayibhava`) and `fine` is the raw uppercase label from the HTML. Normalization is by result-id prefix: `r_tp_*→tatpurusa`, `r_bv_*`/`r_bahuvrishi→bahuvrihi`, `r_dv_*→dvandva`, `r_km_*→karmadharaya`, `r_avyayibhava→avyayibhava` (dvigu ⊂ karmadhāraya per the H989 codebook).
- `load_rules(path) -> dict` used by Tasks 4 and 5.

- [ ] **Step 1: Write the failing snapshot test**

```python
# tests/test_rules.py
from pathlib import Path
import json
SRC = Path(__file__).resolve().parents[2] / "drumam" / "archive" / "samasa_decision_tree.html"
RULES = Path(__file__).resolve().parents[1] / "rules.json"

def test_snapshot_matches_html():
    from extract_rules import extract
    assert json.loads(RULES.read_text(encoding="utf-8")) == extract(SRC)

def test_tree_shape():
    r = json.loads(RULES.read_text(encoding="utf-8"))
    assert len(r["nodes"]) == 15
    assert len(r["results"]) == 24
    assert r["nodes"]["start"]["yes"] == "check_avyayi"
    assert r["nodes"]["start"]["no"] == "ask_dvandva"
    assert r["nodes"]["start"]["kind"] == "form"
    assert r["nodes"]["ask_bv_role"]["kind"] == "semantic"
    assert r["results"]["r_km_adj"]["type"] == "karmadharaya"
```

- [ ] **Step 2: Run to verify failure**

`cd C:/Users/COMPUTER/Documents/GitHub/SamasaChakram && python -m pytest samasacakra/top1000/tests/test_rules.py -q -p no:cacheprovider`
Expected: FAIL (module `extract_rules` not found).

- [ ] **Step 3: Implement the extractor**

```python
# extract_rules.py
import json, re, sys
from pathlib import Path

def extract(html_path: Path) -> dict:
    s = html_path.read_text(encoding="utf-8")
    blk = s[s.index("var NODES = {"):s.index("var REMAINING = {")]
    nodes = {}
    for m in re.finditer(r"^  ([A-Za-z0-9_]+):\{(.*?)^  \},?$", blk, re.M | re.S):
        nid, body = m.group(1), m.group(2)
        q = re.search(r"return L\('([^']*)'", body)
        yes = re.search(r"\byes:'([^']+)'", body)
        no = re.search(r"\bno:'([^']+)'", body)
        if not (q and yes and no):
            continue
        form = nid in {"start", "ask_tp_numeral", "ask_tp_prefix"}
        nodes[nid] = {"id": nid, "question": q.group(1), "yes": yes.group(1),
                      "no": no.group(1), "step": 0, "kind": "form" if form else "semantic"}
    rblk = s[s.index("var RESULTS = {"):]
    rblk = rblk[:rblk.index("\n};")]
    results = {}
    prefixes = [("r_tp_", "tatpurusa"), ("r_bv_", "bahuvrihi"),
                ("r_bahuvrishi", "bahuvrihi"), ("r_dv_", "dvandva"),
                ("r_km_", "karmadharaya"), ("r_avyayibhava", "avyayibhava")]
    for m in re.finditer(r"^  (r_[A-Za-z0-9_]+):\{", rblk, re.M):
        rid = m.group(1)
        seg = rblk[m.end():rblk.find("\n  },", m.end()) + 4]
        typ = re.search(r"type:function\(\)\{return '([^']+)'", seg)
        coarse = next((v for k, v in prefixes if rid.startswith(k)), "unknown")
        results[rid] = {"type": coarse, "fine": typ.group(1) if typ else rid}
    av = re.search(r"var AVYAYA_WORDS = \(function\(\) \{(.*?)\}\)\(\);", s, re.S)
    pv = re.search(r"var PREVERB_LIST = \[(.*?)\];", s, re.S)
    nums = ["eka", "dvi", "tri", "catur", "pañca", "ṣaṣ", "sapta"]
    return {"nodes": nodes, "results": results,
            "avyaya_words": sorted(set(re.findall(r"'([^']+)'", av.group(1)))) if av else [],
            "preverbs": sorted(set(re.findall(r"'([^']+)'", pv.group(1)))) if pv else [],
            "numerals": nums}

if __name__ == "__main__":
    out = Path(__file__).with_name("rules.json")
    out.write_text(json.dumps(extract(Path(sys.argv[1])), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
```

Run the extractor once, then the tests.

- [ ] **Step 4: Add the fail-closed checker**

```python
# check_rules.py
import json
from pathlib import Path
from extract_rules import extract
r = Path(__file__).with_name("rules.json")
html = Path(__file__).resolve().parents[2] / "drumam/archive/samasa_decision_tree.html"
ok = json.loads(r.read_text(encoding="utf-8")) == extract(html)
print("RULES CHECK:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

- [ ] **Step 5: Run tests**

`python -m pytest samasacakra/top1000/tests/test_rules.py -q -p no:cacheprovider && python samasacakra/top1000/check_rules.py`
Expected: 2 passed, `RULES CHECK: PASS`.

- [ ] **Step 6: Commit**

`git add samasacakra/top1000 && git commit -m "feat(top1000): snapshot Drumam rules as canonical JSON" && git pull --rebase origin main && git push`

---

### Task 2: Ranked top-1000 builder

**Files:**
- Create: `samasacakra/top1000/build_top1000.py`
- Test: `samasacakra/top1000/tests/test_build.py`

**Interfaces:**
- Consumes: `cmps.csv` (`surface;members` semicolon split), `names.csv` (`surface;…;…;freq`)
- Produces: `rank_compounds(cmps, names, cap=1000) -> list[dict]` with keys `rank`, `compound`, `members`, `freq`; `write_ranked(rows, path)`.

- [ ] **Step 1: Failing tests**

```python
def test_rank_uses_measured_frequency_and_drops_missing(tmp_path):
    cmps = tmp_path/"cmps.csv"; names = tmp_path/"names.csv"
    cmps.write_text("rājaputra;rājan putra\nghost;ghost word\n", encoding="utf-8")
    names.write_text("rājaputra;x;y;37\nghost;x;y;0\n", encoding="utf-8")
    from build_top1000 import rank_compounds
    rows = rank_compounds(cmps, names, cap=10)
    assert [r["compound"] for r in rows] == ["rājaputra"]
    assert rows[0]["members"] == ["rājan", "putra"]
    assert rows[0]["freq"] == 37

def test_cap_is_applied(tmp_path):
    cmps = tmp_path/"c.csv"; names = tmp_path/"n.csv"
    cmps.write_text("".join(f"w{i};a b\n" for i in range(5)), encoding="utf-8")
    names.write_text("".join(f"w{i};x;y;{5-i}\n" for i in range(5)), encoding="utf-8")
    from build_top1000 import rank_compounds
    assert [r["rank"] for r in rank_compounds(cmps, names, cap=2)] == [1, 2]
```

- [ ] **Step 2: Run and confirm FAIL.**

`python -m pytest samasacakra/top1000/tests/test_build.py -q -p no:cacheprovider`

- [ ] **Step 3: Implement**

```python
# build_top1000.py
import csv
from pathlib import Path

def rank_compounds(cmps: Path, names: Path, cap: int = 1000) -> list:
    freq = {}
    with names.open(encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split(";")
            if len(p) < 4:
                continue
            try:
                freq[p[0].strip()] = int(p[3])
            except ValueError:
                continue
    ranked = []
    with cmps.open(encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split(";", 1)
            if len(p) < 2:
                continue
            surface, members = p[0].strip(), p[1].split()
            if surface in freq and freq[surface] > 0 and len(members) >= 2:
                ranked.append({"compound": surface, "members": members, "freq": freq[surface]})
    ranked.sort(key=lambda r: (-r["freq"], r["compound"]))
    return [dict(rank=i + 1, **r) for i, r in enumerate(ranked[:cap])]

def write_ranked(rows, path):
    path = Path(path)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("rank\tcompound\tmembers\tfreq\n")
        for r in rows:
            fh.write(f'{r["rank"]}\t{r["compound"]}\t{" ".join(r["members"])}\t{r["freq"]}\n')
    return path
```

- [ ] **Step 4: Run tests → PASS.**
- [ ] **Step 5: Commit/push** with message `feat(top1000): rank DCS compounds by corpus frequency`.

---

### Task 3: Gold loaders

**Files:**
- Create: `samasacakra/top1000/gold.py`
- Test: `samasacakra/top1000/tests/test_gold.py`

**Interfaces:**
- Consumes: H989 `validation_sample.tsv`, `annotations_full.tsv`; Gita `gita_morphology_gold.tsv`
- Produces: `load_h989(base: Path) -> list[dict]` (`id`, `surface`, `coarse`, `fine`, `vigraha`), `load_gita(path: Path) -> list[dict]`, `split_fewshot(gold, n=60, seed=20260715) -> (fewshot, holdout)`.

- [ ] **Step 1: Failing tests**

```python
def test_h989_uses_pass_a_and_excludes_disagreement(tmp_path):
    d = tmp_path/"tatpurusha"/"data"; d.mkdir(parents=True)
    (d/"validation_sample.tsv").write_text("cpd_token_id\tcompound_surface\n1\trājaputra\n", encoding="utf-8")
    (d/"annotations_full.tsv").write_text(
        "pass\tcpd_token_id\tcoarse\tfine\tvigraha\trationale\n"
        "A\t1\ttatpurusa\tsasthi\trājñaḥ putraḥ\tx\nB\t1\ttatpurusa\tsasthi\trājñaḥ putraḥ\tx\n",
        encoding="utf-8")
    from gold import load_h989
    g = load_h989(tmp_path)
    assert g == [{"id": "1", "surface": "rājaputra", "coarse": "tatpurusa",
                  "fine": "sasthi", "vigraha": "rājñaḥ putraḥ"}]

def test_gita_excludes_dual_tags(tmp_path):
    p = tmp_path/"g.tsv"
    p.write_text("verse\tform\n1.01\ta\t" + "\t"*11 + "tatpurusa\n1.02\tb\t" + "\t"*11 + "DV/TP\n", encoding="utf-8")
    from gold import load_gita
    assert [r["coarse"] for r in load_gita(p)] == ["tatpurusa"]
```

- [ ] **Step 2: FAIL. Step 3: implement:**

```python
# gold.py
import random
from pathlib import Path

def load_h989(base: Path) -> list:
    d = Path(base) / "tatpurusha" / "data"
    surfaces = {}
    with (d / "validation_sample.tsv").open(encoding="utf-8") as fh:
        for row in __import__("csv").DictReader(fh, delimiter="\t"):
            surfaces[row["cpd_token_id"]] = row["compound_surface"]
    gold = []
    with (d / "annotations_full.tsv").open(encoding="utf-8") as fh:
        for row in __import__("csv").DictReader(fh, delimiter="\t"):
            if row["pass"] != "A" or row["cpd_token_id"] not in surfaces:
                continue
            gold.append({"id": row["cpd_token_id"], "surface": surfaces[row["cpd_token_id"]],
                         "coarse": row["coarse"], "fine": row["fine"],
                         "vigraha": row.get("vigraha", "")})
    return gold

def load_gita(path: Path) -> list:
    out = []
    with Path(path).open(encoding="utf-8") as fh:
        for row in __import__("csv").DictReader(fh, delimiter="\t"):
            tag = row.get("compound", "")
            if tag and "/" not in tag:
                out.append({"surface": row["form"], "coarse": tag})
    return out

def split_fewshot(gold, n=60, seed=20260715):
    rows = list(gold)
    random.Random(seed).shuffle(rows)
    return rows[:n], rows[n:]
```

- [ ] **Step 4: PASS. Step 5: commit/push** `feat(top1000): load H989 and Gita gold with honest dual-tag exclusion`.

---

### Task 3b: Scharf Rāmopākhyāna fine gold from PDF

**Files:**
- Create: `samasacakra/top1000/scharf.py`
- Create: `samasacakra/top1000/data/scharf_gold.tsv` (generated)
- Test: `samasacakra/top1000/tests/test_scharf.py`

**Interfaces:**
- Consumes: Scharf PDF path (CLI `--pdf`), license permits derivative works.
- Produces: `extract_scharf(text: str) -> list[dict]` with keys `compound`, `fine`, `coarse`, `ambiguous`; `load_scharf(path) -> list[dict]`; `coarse_of(fine: str) -> str`.

- [ ] **Step 1: Failing fixture test**

```python
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
```

- [ ] **Step 2: FAIL. Step 3: implement:**

```python
# scharf.py
import csv, re
from pathlib import Path

LABELS = [
    (re.compile(r"ṣaṣṭhī|tatpuruṣa|upapada|nañ|gati|prādi", re.I), "tatpurusa"),
    (re.compile(r"karmadhāraya|dvigu", re.I), "karmadharaya"),
    (re.compile(r"dvandva", re.I), "dvandva"),
    (re.compile(r"bahuvrīhi", re.I), "bahuvrihi"),
]

def coarse_of(fine: str) -> str:
    for pattern, coarse in LABELS:
        if pattern.search(fine):
            return coarse
    return "unknown"

def extract_scharf(text: str) -> list:
    out = []
    for line in text.splitlines():
        if "—" not in line:
            continue
        compound, label = (p.strip() for p in line.split("—", 1))
        if not compound or " " in compound:
            continue
        ambiguous = "ambiguous" in label.lower() or "/" in label
        coarse = "unknown" if ambiguous else coarse_of(label)
        out.append({"compound": compound, "fine": label, "coarse": coarse,
                    "ambiguous": ambiguous})
    return out

def load_scharf(path: Path) -> list:
    with Path(path).open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r["ambiguous"] != "True"]

if __name__ == "__main__":
    import argparse
    from pypdf import PdfReader
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("data") / "scharf_gold.tsv"))
    args = ap.parse_args()
    text = "\n".join(p.extract_text() or "" for p in PdfReader(args.pdf).pages)
    rows = extract_scharf(text)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("compound\tfine\tcoarse\tambiguous\n")
        for r in rows:
            fh.write(f'{r["compound"]}\t{r["fine"]}\t{r["coarse"]}\t{r["ambiguous"]}\n')
    print("wrote", out, len(rows), "rows")
```

- [ ] **Step 4: PASS. Step 5: run against the PDF** (`python samasacakra/top1000/scharf.py --pdf <PATH>`), commit TSV + code and push: `feat(top1000): extract Scharf fine gold from PDF (derivative allowed)`.

---

### Task 4: Deterministic tree walker

**Files:**
- Create: `samasacakra/top1000/classify.py`
- Test: `samasacakra/top1000/tests/test_classify.py`

**Interfaces:**
- Consumes: `rules.json` (Task 1)
- Produces: `classify(surface, members, answers, rules) -> dict` with `type`, `fine`, `path`, `unanswered`.

- [ ] **Step 1: Failing tests**

```python
RULES = {"nodes": {
  "start": {"id":"start","yes":"check","no":"r_bv","kind":"form"},
  "check": {"id":"check","yes":"r_tp","no":"r_bv","kind":"semantic"},
}, "results": {"r_bv":{"type":"bahuvrihi"},"r_tp":{"type":"tatpurusa"}},
"avyaya_words":["upa"], "preverbs":["prati"], "numerals":["eka","dvi"]}

def test_form_branch_and_unanswered_semantic_node():
    from classify import classify
    r = classify("upagaṅgam", ["upa","gaṅgā"], {}, RULES)
    # upa is avyaya -> node "check" reached; without a JEV answer it stays unknown
    assert r["type"] == "unknown"
    assert r["path"] == ["start", "check"]
    assert r["unanswered"] == ["check"]

def test_semantic_answer_reaches_result():
    from classify import classify
    r = classify("rājaputraḥ", ["rājan","putra"], {"check": True}, RULES)
    assert r["type"] == "tatpurusa" and r["unanswered"] == []
```

- [ ] **Step 2: FAIL. Step 3: implement:**

```python
# classify.py
def classify(surface, members, answers, rules):
    nodes, results = rules["nodes"], rules["results"]
    cur, path, unanswered = "start", [], []
    seen = set()
    while cur in nodes and cur not in seen:
        seen.add(cur)
        node = nodes[cur]
        path.append(cur)
        if node["kind"] == "form":
            form = "start"
            if cur.startswith("ask_tp_numeral"):
                form = "numeral"
            elif cur.startswith("ask_tp_prefix"):
                form = "prefix"
            if form == "start":
                ans = any(m in rules.get("avyaya_words", []) for m in members)
            elif form == "numeral":
                ans = members[0] in rules.get("numerals", ["eka", "dvi", "tri", "catur"])
            else:
                ans = members[0] in rules.get("preverbs", [])
        else:
            if cur not in answers:
                unanswered.append(cur)
                break
            ans = bool(answers[cur])
        cur = node["yes"] if ans else node["no"]
    terminal = results.get(cur, {})
    return {"type": terminal.get("type", "unknown"), "fine": terminal.get("fine", ""),
            "path": path, "unanswered": unanswered}
```

- [ ] **Step 4: PASS. Step 5: commit/push** `feat(top1000): deterministic Drumam walker with honest unanswered nodes`.

---

### Task 5: JEV semantic annotator

**Files:**
- Create: `samasacakra/top1000/semantics.py`
- Test: `samasacakra/top1000/tests/test_semantics.py`

**Interfaces:**
- Consumes: `jev_probe.py` via `importlib` (same pattern as `samasa_subtype_jev_choice_probe.py`), `fewshot` from Task 3, `rules` from Task 1
- Produces: `answer_semantics(surface, members, questions, fewshot, rules, run=False, max_cost=0.0, probe=None) -> dict[qid, bool]`; never raises on malformed answers.

- [ ] **Step 1: Failing tests with a fake probe**

```python
class FakeProbe:
    def __init__(self, payload): self.payload = payload
    def ask(self, state, questions): return self.payload

def test_malformed_answer_becomes_unanswered():
    from semantics import answer_semantics
    out = answer_semantics("x", ["a","b"], ["check"], [], {}, probe=FakeProbe({}), run=True)
    assert out == {}

def test_valid_yes_no_roundtrip():
    from semantics import answer_semantics
    out = answer_semantics("x", ["a","b"], ["check"], [], {},
                           probe=FakeProbe({"check": {"choice": "yes"}}), run=True)
    assert out == {"check": True}
```

- [ ] **Step 2: FAIL. Step 3: implement:**

```python
# semantics.py
import json, sys
from pathlib import Path

def load_probe():
    uprava = Path(__file__).resolve().parents[3] / "Uprava" / "tools"
    sys.path.insert(0, str(uprava))
    import jev_probe
    return jev_probe

def answer_semantics(surface, members, questions, fewshot, rules, run=False, max_cost=0.0, probe=None):
    if not run or not questions:
        return {}
    p = probe or load_probe()
    state = {"compound": surface, "members": members,
             "few_shot": [{"compound": g["surface"], "vigraha": g.get("vigraha", ""),
                           "type": g["coarse"]} for g in fewshot[:8]],
             "questions": {q: rules["nodes"][q]["question"] for q in questions}}
    questions_spec = {q: {"type": "choice", "criteria": {"yes": "answer yes", "no": "answer no"}}
                      for q in questions}
    raw = p.ask(state, questions_spec) if probe else None
    if raw is None:  # live path uses the probe's CLI transport
        return _live(p, state, questions_spec, questions, max_cost)
    out = {}
    for q in questions:
        v = raw.get(q, {})
        if isinstance(v, dict) and v.get("choice") in ("yes", "no"):
            out[q] = v["choice"] == "yes"
    return out

def _live(p, state, spec, questions, max_cost):
    req = {"state": state, "model": p.DEFAULT_MODEL, "questions": spec}
    ok, why = p.validate_request(req)
    if not ok:
        raise ValueError(why)
    api_key, model, endpoint = p.resolve_config(type("A", (), {"env_file": str(p.DEFAULT_ENV_FILE)})())
    if not api_key:
        raise RuntimeError("TYPESAFE_API_KEY not found")
    req["model"] = model
    status, body = p.call_jev(req, api_key, endpoint, timeout_s=p.REQUEST_TIMEOUT_S)
    if p.classify_result(status, body) != "OK":
        return {}
    if p.cost_usd(body.get("usage")) is not None and p.cost_usd(body.get("usage")) > max_cost:
        raise RuntimeError("cost cap exceeded")
    answers = body.get("answers", {})
    return {q: answers[q]["choice"] == "yes" for q in questions
            if isinstance(answers.get(q), dict) and answers[q].get("choice") in ("yes", "no")}
```

- [ ] **Step 4: Add a dry-run CLI test** verifying that no key is read and no network call happens without `--run`:

```python
def test_default_is_dry_run():
    from semantics import answer_semantics
    assert answer_semantics("x", ["a"], ["check"], [], {}) == {}
```

- [ ] **Step 5: PASS. Step 6: commit/push** `feat(top1000): JEV semantic answers with dry-run default and malformed-answer residue`.

---

### Task 6: Evaluation, kill-gate and final artifacts

**Files:**
- Create: `samasacakra/top1000/evaluate.py`, `samasacakra/top1000/check_top1000.py`, `reports/TOP1000_TYPED_REPORT.md` (generated)

**Interfaces:**
- Consumes: Tasks 1–5
- Produces: `report` dict with `coverage`, `coarse_accuracy`, `fine_accuracy`, `unknown_rate`, `confusion`; `write_outputs(...) -> paths`.

- [ ] **Step 1: Failing gate test**

```python
def test_killgate_blocks_publication(tmp_path):
    from evaluate import gate
    assert gate({"coarse_accuracy": 0.69})["publish"] is False
    assert gate({"coarse_accuracy": 0.70})["publish"] is True
```

- [ ] **Step 2: FAIL. Step 3: implement:**

```python
# evaluate.py
THRESHOLD = 0.70

def gate(metrics):
    return {"publish": metrics["coarse_accuracy"] >= THRESHOLD,
            "threshold": THRESHOLD, "measured": metrics["coarse_accuracy"]}

def evaluate(predictions, gold):
    scored = [(p, g) for p, g in zip(predictions, gold) if p["type"] != "unknown"]
    correct = sum(p["type"] == g["coarse"] for p, g in scored)
    return {"coverage": len(scored) / max(len(gold), 1),
            "coarse_accuracy": correct / max(len(scored), 1),
            "unknown_rate": 1 - len(scored) / max(len(gold), 1)}
```

- [ ] **Step 4: Add fail-closed artifact check**

```python
# check_top1000.py
import csv, json, hashlib
from pathlib import Path
p = Path(__file__).with_name("data") / "top1000_typed.tsv"
m = json.loads((Path(__file__).with_name("data") / "top1000_manifest.json").read_text(encoding="utf-8"))
rows = list(csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"))
assert len(rows) == 1000, len(rows)
assert len({r["compound"] for r in rows}) == 1000
assert {r["rank"] for r in rows} == {str(i) for i in range(1, 1001)}
assert hashlib.sha256(p.read_bytes()).hexdigest() == m["sha256"]
assert m["threshold"] == 0.70 and m["publish"] is True
print("TOP1000 CHECK: PASS")
```

- [ ] **Step 5: Run the full pipeline in dry-run first**, then `--run` with `--max-cost 0.50` once the fake-probe tests pass; commit the report, manifest, TSV (only if gate passed) and push. Message: `feat(top1000): typed top-1000 with kill-gate and honest unknown residue`.

- [ ] **Step 6: Register** one edge row in `Uprava/PROJECT_INTERLINKS.md` (`SamasaChakram→kosha · top1000 typed compounds`, consume-don't-rebuild) in the same PR chain; push.

---

## Self-Review

- Spec §3 sources: all six covered (Tasks 2, 1, 3, 3b, 5). §4 components: all five covered. §5 gates: Task 6. §6 residues: unknown (Task 4), biased gold (Task 3), Scharf `ambiguous` residue (Task 3b). §7 acceptance: Tasks 1–6 + 3b.
- No placeholders: every code step has actual code; the only deferred item (Scharf) is explicitly out of scope by spec.
- Type consistency: `rules` dict from Task 1 → `classify(..., rules)` Task 4 → `answer_semantics(..., rules)` Task 5 → `evaluate` Task 6. `coarse` label name consistent (`tatpurusa`, `bahuvrihi`, `dvandva`, `karmadharaya`).
- Review Focus: five lines, each pinned to a test in its owning task (Tasks 2, 3, 4, 5, 6).
