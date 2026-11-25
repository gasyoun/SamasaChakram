import argparse
import hashlib
import json
from pathlib import Path

from build_top1000 import combine_rankings, rank_from_lemma_proxy, rank_from_wordfreq
from batch import batched, classify_batch
from evaluate import evaluate, gate
from gold import load_h989, split_fewshot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmps", required=True)
    ap.add_argument("--freq", required=True)
    ap.add_argument("--lemma-freq", default="", help="DCS lemma TSV for member-frequency proxy fill")
    ap.add_argument("--gold-base", required=True)
    ap.add_argument("--rules", default=str(Path(__file__).with_name("rules.json")))
    ap.add_argument("--out-dir", default=str(Path(__file__).with_name("data")))
    ap.add_argument("--run", action="store_true", help="live JEV calls (default: dry-run)")
    ap.add_argument("--max-cost", type=float, default=0.50)
    ap.add_argument("--limit", type=int, default=0, help="debug cap on ranked items")
    args = ap.parse_args()

    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    fewshot, holdout = split_fewshot(load_h989(Path(args.gold_base)), n=60, seed=20260715)
    measured = rank_from_wordfreq(Path(args.cmps), Path(args.freq), cap=1000,
                                  extra_stop=rules["avyaya_words"])
    if args.lemma_freq:
        proxy = rank_from_lemma_proxy(Path(args.cmps), Path(args.lemma_freq), cap=1000,
                                      extra_stop=rules["avyaya_words"])
        ranked = combine_rankings(measured, proxy, cap=1000)
    else:
        ranked = measured
    if args.limit:
        ranked = ranked[:args.limit]

    val_items = [{"surface": g["surface"], "members": [g["surface"]]} for g in holdout]
    val_preds = []
    for chunk in batched(val_items, 10):
        val_preds.extend(classify_batch(chunk, rules, fewshot, args.run, args.max_cost))
    metrics = evaluate(val_preds, holdout)
    verdict = gate(metrics)
    print("VALIDATION", json.dumps({**metrics, **verdict}, ensure_ascii=False))

    mode = "live" if args.run else "dry-run"
    ranked_items = [{"surface": r["compound"], "members": r["members"]} for r in ranked]
    results = []
    for chunk in batched(ranked_items, 10):
        results.extend(classify_batch(chunk, rules, fewshot, args.run, args.max_cost))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = out / "TOP1000_TYPED_REPORT.md"
    report.write_text(
        "# Top-1000 typed samāsa compounds\n\n"
        f"Mode: **{mode}** · Source: DCS Kompozity + word_frequency_norm.txt (CC BY 4.0)\n\n"
        f"Validation on 60 H989 holdout compounds: coverage {metrics['coverage']:.3f}, "
        f"coarse accuracy {metrics['coarse_accuracy']:.3f}, unknown rate {metrics['unknown_rate']:.3f}.\n"
        f"Kill-gate (≥0.70): {'PASS' if verdict['publish'] else 'FAIL'}.\n\n"
        f"Ranking basis: {sum(r.get('basis') == 'measured' for r in ranked)} rows with "
        "measured DCS compound-surface frequency; "
        f"{sum(r.get('basis') == 'lemma_proxy' for r in ranked)} rows by min DCS lemma "
        "frequency of members (PROXY, not attested compound frequency).\n\n"
        "Types are classifier outputs, not corpus annotations (FINDINGS §449). "
        "No type-frequency claim is made.\n", encoding="utf-8")

    if verdict["publish"] and args.run:
        tsv = out / "top1000_typed.tsv"
        with tsv.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write("rank\tcompound\tmembers\tfreq\ttype_coarse\ttype_fine\tconfidence\t"
                     "decision_path\tsource\tgold_agree\tlicense\n")
            for r, c in zip(ranked, results):
                fh.write("\t".join([str(r["rank"]), r["compound"], " ".join(r["members"]),
                                    str(r["freq"]), c["type"], c["fine"], "",
                                    " > ".join(c["path"]), "drumam+jev", "", "CC BY 4.0"]) + "\n")
        manifest = {"sha256": hashlib.sha256(tsv.read_bytes()).hexdigest(),
                    "threshold": 0.70, "publish": True, "mode": mode,
                    "rows": len(results),
                    "source": ["cmps.csv", "word_frequency_norm.txt"],
                    "basis_counts": {b: sum(r.get("basis") == b for r in ranked)
                                     for b in ("measured", "lemma_proxy")},
                    "validation": metrics}
        (out / "top1000_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote", tsv, len(results), "rows")
    else:
        print("typed TSV NOT published (gate failed or dry-run)")


if __name__ == "__main__":
    main()
