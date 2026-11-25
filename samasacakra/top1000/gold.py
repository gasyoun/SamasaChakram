import csv
import random
from pathlib import Path


def load_h989(base: Path) -> list:
    d = Path(base) / "tatpurusha" / "data"
    surfaces = {}
    with (d / "validation_sample.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            surfaces[row["cpd_token_id"]] = row["compound_surface"]
    gold = []
    with (d / "annotations_full.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["pass"] != "A" or row["cpd_token_id"] not in surfaces:
                continue
            gold.append({"id": row["cpd_token_id"], "surface": surfaces[row["cpd_token_id"]],
                         "coarse": row["coarse"], "fine": row["fine"],
                         "vigraha": row.get("vigraha", "")})
    return gold


def load_gita(path: Path) -> list:
    out = []
    with Path(path).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            tag = row.get("compound", "")
            if tag and "/" not in tag:
                out.append({"surface": row["form"], "coarse": tag})
    return out


def split_fewshot(gold, n=60, seed=20260715):
    rows = list(gold)
    random.Random(seed).shuffle(rows)
    return rows[:n], rows[n:]
