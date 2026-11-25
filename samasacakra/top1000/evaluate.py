THRESHOLD = 0.70


def gate(metrics):
    return {"publish": metrics["coarse_accuracy"] >= THRESHOLD,
            "threshold": THRESHOLD, "measured": metrics["coarse_accuracy"]}


def evaluate(predictions, gold):
    scored = [(p, g) for p, g in zip(predictions, gold) if p["type"] != "unknown"]
    correct = sum(p["type"] == g["coarse"] for p, g in scored)
    total = max(len(gold), 1)
    return {"n": len(gold), "coverage": len(scored) / total,
            "coarse_accuracy": correct / max(len(scored), 1),
            "unknown_rate": 1 - len(scored) / total,
            "correct": correct, "scored": len(scored)}
