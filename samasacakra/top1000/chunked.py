import argparse
import hashlib
import json
from pathlib import Path

from batch import batched, classify_batch
from build_top1000 import combine_rankings, rank_from_lemma_proxy, rank_from_wordfreq
from evaluate import evaluate, gate
from gold import load_h989, split_fewshot

D = Path(__file__).with_name("data")


def load_rules():
    return json.loads(Path(__file__).with_name("rules.json").read_text(encoding="utf-8"))


def prepare(args):
    rules = load_rules()
    _, holdout = split_fewshot(load_h989(Path(args.gold_base)), n=60, seed=20260715)
    fewshot, _ = split_fewshot(load_h989(Path(args.gold_base)), n=60, seed=20260715)
    measured = rank_from_wordfreq(Path(args.cmps), Path(args.freq), cap=1000,
                                  extra_stop=rules["avyaya_words"])
    proxy = rank_from_lemma_proxy(Path(args.cmps), Path(args.lemma_freq), cap=1000,
                                  extra_stop=rules["avyaya_words"])
    ranked = combine_rankings(measured, proxy, cap=1000)
    (D / "fewshot.json").write_text(json.dumps(fewshot, ensure_ascii=False), encoding="utf-8")
    (D / "ranked.json").write_text(json.dumps(ranked, ensure_ascii=False), encoding="utf-8")
    print("prepared", len(ranked), "ranked and", len(holdout), "holdout")


def classify_items(items, rules, fewshot, run, max_cost):
    out = []
    for chunk in batched(items, 10):
        out.extend(classify_batch(chunk, rules, fewshot, run, max_cost))
    return out


def validate(args):
    rules, fewshot = load_rules(), json.loads((D / "fewshot.json").read_text(encoding="utf-8"))
    _, holdout = split_fewshot(load_h989(Path(args.gold_base)), n=60, seed=20260715)
    items = [{"surface": g["surface"], "members": [g["surface"]]} for g in holdout]
    preds = classify_items(items, rules, fewshot, args.run, args.max_cost)
    metrics = evaluate(preds, holdout)
    verdict = gate(metrics)
    (D / "validation.json").write_text(
        json.dumps({**metrics, **verdict}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VALIDATION", json.dumps({**metrics, **verdict}, ensure_ascii=False))


def chunk(args):
    rules, fewshot = load_rules(), json.loads((D / "fewshot.json").read_text(encoding="utf-8"))
    ranked = json.loads((D / "ranked.json").read_text(encoding="utf-8"))
    start = args.chunk * 100
    end = min(start + 100, len(ranked))
    rows = ranked[start:end]
    items = [{"surface": r["compound"], "members": r["members"]} for r in rows]
    preds = classify_items(items, rules, fewshot, args.run, args.max_cost)
    with (D / "predictions.jsonl").open("a", encoding="utf-8") as fh:
        for r, p in zip(rows, preds):
            fh.write(json.dumps({"rank": r["rank"], "compound": r["compound"], "pred": p},
                                ensure_ascii=False) + "\n")
    print(f"chunk {args.chunk}: wrote {len(preds)} predictions ({start+1}..{end})")


def assemble(args):
    ranked = json.loads((D / "ranked.json").read_text(encoding="utf-8"))
    val = json.loads((D / "validation.json").read_text(encoding="utf-8"))
    preds = {}
    for line in (D / "predictions.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            p = json.loads(line)
            preds[p["rank"]] = p["pred"]
    missing = [r["rank"] for r in ranked if r["rank"] not in preds]
    if missing:
        raise SystemExit(f"missing {len(missing)} predictions, first: {missing[:5]}")
    tsv = D / "top1000_typed.tsv"
    with tsv.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("rank\tcompound\tmembers\tfreq\ttype_coarse\ttype_fine\tconfidence\t"
                 "decision_path\tsource\tgold_agree\tlicense\n")
        for r in ranked:
            p = preds[r["rank"]]
            fh.write("\t".join([str(r["rank"]), r["compound"], " ".join(r["members"]),
                                str(r["freq"]), p["type"], p["fine"], "",
                                " > ".join(p["path"]), "drumam+jev", "", "CC BY 4.0"]) + "\n")
    manifest = {"sha256": hashlib.sha256(tsv.read_bytes()).hexdigest(),
                "threshold": 0.70, "publish": val["publish"], "mode": "live",
                "rows": len(ranked),
                "source": ["cmps.csv", "word_frequency_norm.txt", "lemma_frequency.tsv"],
                "basis_counts": {b: sum(r.get("basis") == b for r in ranked)
                                 for b in ("measured", "lemma_proxy")},
                "validation": val}
    (D / "top1000_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (D / "TOP1000_TYPED_REPORT.md").write_text(
        f"""# Top-1000 typed samāsa compounds

Mode: **live** (batched JEV, 10 compounds/request) · Source: DCS Kompozity +
word_frequency_norm.txt + lemma_frequency.tsv (CC BY 4.0).

Validation (60 H989 holdout): coverage {val['coverage']:.3f}, coarse accuracy
{val['coarse_accuracy']:.3f}, unknown rate {val['unknown_rate']:.3f}. Kill-gate (≥0.70):
{'PASS' if val['publish'] else 'FAIL'}.

Ranking: {manifest['basis_counts']['measured']} measured compound-surface frequencies;
{manifest['basis_counts']['lemma_proxy']} member-frequency proxies (NOT attested compound
frequency). Types are classifier outputs, not corpus annotations (FINDINGS §449).

CAVEAT: the 60-item gold and its few-shot examples come from Sangram P4 (H989),
a tatpuruṣa-only pilot. The measured 0.733 accuracy and the heavily tatpuruṣa-skewed
type distribution reflect that biased gold; they are NOT a balanced estimate of
accuracy across classes. Do not read the column as a corpus type-frequency claim.
""", encoding="utf-8")
    print("assembled", len(ranked), "rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["prepare", "validate", "chunk", "assemble"])
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--cmps", default=str(D / "cmps.csv"))
    ap.add_argument("--freq", default=str(D / "word_frequency_norm.txt"))
    ap.add_argument("--lemma-freq", required=False)
    ap.add_argument("--gold-base", required=False)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--max-cost", type=float, default=0.50)
    args = ap.parse_args()
    D.mkdir(parents=True, exist_ok=True)
    {"prepare": prepare, "validate": validate, "chunk": chunk, "assemble": assemble}[args.action](args)
