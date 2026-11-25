import json
from pathlib import Path

from extract_rules import extract

r = Path(__file__).with_name("rules.json")
html = Path(__file__).resolve().parents[2] / "drumam/archive/samasa_decision_tree.html"
ok = json.loads(r.read_text(encoding="utf-8")) == extract(html)
print("RULES CHECK:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
