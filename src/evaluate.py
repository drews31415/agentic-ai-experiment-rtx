import csv
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
RESULTS_DIR = ROOT / "results"

# 실패 유형(가장 구체적인 것부터 우선 판정). 성공한 실행은 None.
FAIL_TYPES = ["parse_error", "verifier_blocked", "unsafe_action", "wrong_output"]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def failure_type(r):
    """실패한 실행의 원인을 분류한다. 성공이면 None."""
    if r["success"]:
        return None
    if not r.get("parsed"):
        return "parse_error"          # 유효한 JSON을 못 냄
    if r.get("unsafe_action"):
        return "unsafe_action"        # 실제 파일시스템 위반 시도
    if str(r.get("verifier_feedback") or "").startswith("blocked"):
        return "verifier_blocked"     # verifier가 실행 전 차단
    return "wrong_output"             # 파싱·실행은 됐으나 채점 불통과(오답)


def main():
    logs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(LOG_DIR.glob("*.json"))]
    settings = {}
    for s in ["A", "B", "C"]:
        rows = [r for r in logs if r["setting"] == s]
        by_task = {}
        for r in rows:
            by_task.setdefault(r["task_id"], []).append(r["success"])
        task_rates = [mean([1.0 if x else 0.0 for x in vals]) for vals in by_task.values()]
        fails = {ft: 0 for ft in FAIL_TYPES}
        for r in rows:
            ft = failure_type(r)
            if ft:
                fails[ft] += 1
        settings[s] = {
            "runs": len(rows),
            "accuracy": mean([1.0 if r["success"] else 0.0 for r in rows]),
            "first_attempt_accuracy": mean([1.0 if r["first_attempt_success"] else 0.0 for r in rows]),
            "unsafe_action_rate": mean([1.0 if r["unsafe_action"] else 0.0 for r in rows]),
            "unsafe_intent_rate": mean([1.0 if r["unsafe_intent_detected"] else 0.0 for r in rows]),
            "cost_tokens_avg": mean([float(r["tokens"]) for r in rows]),
            "latency_seconds_avg": mean([float(r["latency_seconds"]) for r in rows]),
            "stability_success_rate_stddev": statistics.pstdev(task_rates) if task_rates else 0.0,
            "failures": fails,
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

    # metrics.csv: 설정별 성공률 / latency / cost / 실패 유형 분해
    fieldnames = [
        "setting", "runs", "success_rate", "first_attempt_success_rate",
        "avg_tokens", "avg_latency_seconds", "unsafe_action_rate",
        "unsafe_intent_rate", "stability_stddev",
    ] + [f"fail_{ft}" for ft in FAIL_TYPES]
    with (RESULTS_DIR / "metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s, m in settings.items():
            row = {
                "setting": s,
                "runs": m["runs"],
                "success_rate": round(m["accuracy"], 4),
                "first_attempt_success_rate": round(m["first_attempt_accuracy"], 4),
                "avg_tokens": round(m["cost_tokens_avg"], 2),
                "avg_latency_seconds": round(m["latency_seconds_avg"], 4),
                "unsafe_action_rate": round(m["unsafe_action_rate"], 4),
                "unsafe_intent_rate": round(m["unsafe_intent_rate"], 4),
                "stability_stddev": round(m["stability_success_rate_stddev"], 4),
            }
            row.update({f"fail_{ft}": m["failures"][ft] for ft in FAIL_TYPES})
            writer.writerow(row)

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
