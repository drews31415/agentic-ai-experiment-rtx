import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "results"


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    logs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(LOG_DIR.glob("*.json"))]
    settings = {}
    for s in ["A", "B", "C"]:
        rows = [r for r in logs if r["setting"] == s]
        by_task = {}
        for r in rows:
            by_task.setdefault(r["task_id"], []).append(r["success"])
        task_rates = [mean([1.0 if x else 0.0 for x in vals]) for vals in by_task.values()]
        settings[s] = {
            "runs": len(rows),
            "accuracy": mean([1.0 if r["success"] else 0.0 for r in rows]),
            "first_attempt_accuracy": mean([1.0 if r["first_attempt_success"] else 0.0 for r in rows]),
            "unsafe_action_rate": mean([1.0 if r["unsafe_action"] else 0.0 for r in rows]),
            "unsafe_intent_rate": mean([1.0 if r["unsafe_intent_detected"] else 0.0 for r in rows]),
            "cost_tokens_avg": mean([float(r["tokens"]) for r in rows]),
            "latency_seconds_avg": mean([float(r["latency_seconds"]) for r in rows]),
            "stability_success_rate_stddev": statistics.pstdev(task_rates) if task_rates else 0.0,
        }
    summary = {
        "log_count": len(logs),
        "settings": settings,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Experiment Report", "", "| setting | runs | accuracy | unsafe action | unsafe intent | avg tokens | avg latency | stability stddev |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s, m in settings.items():
        lines.append(f"| {s} | {m['runs']} | {m['accuracy']:.4f} | {m['unsafe_action_rate']:.4f} | {m['unsafe_intent_rate']:.4f} | {m['cost_tokens_avg']:.2f} | {m['latency_seconds_avg']:.2f} | {m['stability_success_rate_stddev']:.4f} |")
    lines.append("")
    lines.append("A = small model, B = large model, C = small model plus verifier/retry.")
    (RESULTS_DIR / "experiment_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
