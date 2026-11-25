import json
import re
import sys
from pathlib import Path


def extract(html_path: Path) -> dict:
    s = html_path.read_text(encoding="utf-8")
    blk = s[s.index("var NODES = {"):s.index("var REMAINING = {")]
    nodes = {}
    for m in re.finditer(r"^  ([A-Za-z0-9_]+):\{(.*?)^  \},?$", blk, re.M | re.S):
        nid, body = m.group(1), m.group(2)
        q = re.search(r"q:function\(\)\{return L\(\s*'([^']*)'", body, re.S)
        yes = re.search(r"\byes:'([^']+)'", body)
        no = re.search(r"\bno:'([^']+)'", body)
        options = []
        ob = re.search(r"options:\[(.*?)\]", body, re.S)
        if ob:
            for part in re.split(r"\{label:", ob.group(1))[1:]:
                label = re.search(r"L\(\s*'([^']*)'", part, re.S)
                nxt = re.search(r"next:'([^']+)'", part)
                if label and nxt:
                    options.append({"label": label.group(1), "next": nxt.group(1)})
        if not q or (not (yes and no) and not options):
            continue
        form = nid in {"start", "ask_tp_numeral", "ask_tp_prefix"}
        nodes[nid] = {"id": nid, "question": q.group(1) if q else "",
                      "yes": yes.group(1) if yes else "", "no": no.group(1) if no else "",
                      "options": options, "step": 0, "kind": "form" if form else "semantic"}
    rblk = s[s.index("var RESULTS = {"):]
    rblk = rblk[:rblk.index("\n};")]
    results = {}
    prefixes = [("r_tp_", "tatpurusa"), ("r_bv_", "bahuvrihi"),
                ("r_bahuvrishi", "bahuvrihi"), ("r_dv_", "dvandva"),
                ("r_km_", "karmadharaya"), ("r_avyayibhava", "avyayibhava")]
    heads = list(re.finditer(r"^  (r_[A-Za-z0-9_]+):\{", rblk, re.M))
    for i, m in enumerate(heads):
        rid = m.group(1)
        end = heads[i + 1].start() if i + 1 < len(heads) else len(rblk)
        seg = rblk[m.end():end]
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


def load_rules(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    out = Path(__file__).with_name("rules.json")
    out.write_text(json.dumps(extract(Path(sys.argv[1])), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
