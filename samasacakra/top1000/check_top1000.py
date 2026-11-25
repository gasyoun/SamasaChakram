import csv
import hashlib
import json
import sys
from pathlib import Path

COLUMNS = ["rank", "compound", "members", "freq", "type_coarse", "type_fine",
           "confidence", "decision_path", "source", "gold_agree", "license"]


def check(tsv, manifest, expected_rows=1000):
    m = json.loads(Path(manifest).read_text(encoding="utf-8"))
    raw = Path(tsv).read_bytes()
    if hashlib.sha256(raw).hexdigest() != m["sha256"]:
        return False
    if m.get("threshold") != 0.70 or m.get("publish") is not True:
        return False
    rows = list(csv.DictReader(Path(tsv).open(encoding="utf-8"), delimiter="\t"))
    if len(rows) != expected_rows:
        return False
    if list(rows[0].keys()) != COLUMNS:
        return False
    if len({r["compound"] for r in rows}) != expected_rows:
        return False
    if {int(r["rank"]) for r in rows} != set(range(1, expected_rows + 1)):
        return False
    return True


if __name__ == "__main__":
    d = Path(__file__).with_name("data")
    ok = check(d / "top1000_typed.tsv", d / "top1000_manifest.json")
    print("TOP1000 CHECK:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
