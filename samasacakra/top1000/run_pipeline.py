import argparse
import hashlib
import json
from pathlib import Path

from build_top1000 import rank_from_wordfreq
from classify import classify
from evaluate import evaluate, gate
from gold import load_h989, split_fewshot
from semantics import answer_semantics


def semantic_ids(rules):
    return [nid for nid, node in rules["nodes"].items() if node["kind"] == "semantic"]


def classify_one(surface, members, rules, fewshot, run, max_cost):
    questions = semantic_ids(rules)
    answers = answer_semantics(surface, members, questions, fewshot, rules,
                               run=run, max_cost=max_cost)
    return classify(surface, members, answers, rules)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmps", required=True)
    ap.add_argument("--freq", required=True)
    ap.add_argument("--gold-base", required=True)
    ap.add_argument("--rules", default=str(Path(__file__).with_name("rules.json")))
    ap.add_argument("--out-dir", default=str(Path(__file__).with_name("data")))
    ap.add_argument("--run", action="store_true", help="live JEV calls (default: dry-run)")
    ap.add_argument("--max-cost", type=float, default=0.50)
    ap.add_argument("--limit", type=int, default=0, help="debug cap on ranked items")
    args = ap.parse_args()

    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    fewshot, holdout = split_fewshot(load_h989(Path(args.gold_base)), n=60, seed=20260715)
    ranked = rank_from_wordfreq(Path(args.cmps), Path(args.freq), cap=1000,
                                extra_stop=rules["avyaya_words"])
    if args.limit:
        ranked = ranked[:args.limit]

    val_preds = [classify_one(g["surface"], [g["surface"]], rules, fewshot,
                              args.run, args.max_cost) for g in holdout]
    metrics = evaluate(val_preds, holdout)
    verdict = gate(metrics)
    print("VALIDATION", json.dumps({**metrics, **verdict}, ensure_ascii=False))

    mode = "live" if args.run else "dry-run"
    results = [classify_one(r["compound"], r["members"], rules, fewshot,
                            args.run, args.max_cost) for r in ranked]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = out / "TOP1000_TYPED_REPORT.md"
    report.write_text(
        "# Top-1000 typed samāsa compounds\n\n"
        f"Mode: **{mode}** · Source: DCS Kompozity + word_frequency_norm.txt (CC BY 4.0)\n\n"
        f"Validation on 60 H989 holdout compounds: coverage {metrics['coverage']:.3f}, "
        f"coarse accuracy {metrics['coarse_accuracy']:.3f}, unknown rate {metrics['unknown_rate']:.3f}.\n"
        f"Kill-gate (≥0.70): {'PASS' if verdict['publish'] else 'FAIL'}.\n\n"
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
                    "rows": len(results), "source": ["cmps.csv", "word_frequency_norm.txt"],
                    "validation": metrics}
        (out / "top1000_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote", tsv, len(results), "rows")
    else:
        print("typed TSV NOT published (gate failed or dry-run)")


if __name__ == "__main__":
    main()
