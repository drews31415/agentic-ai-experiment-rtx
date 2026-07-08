"""전체 실험 러너.

세 설정을 모두 실행하고 실행별 로그를 logs/에 저장한다.
    A = baseline(작은 모델)         → baseline.run_baseline_task
    B = baseline(큰 모델)           → baseline.run_baseline_task
    C = baseline + verifier         → verifier.run_verified_task

지표 집계는 evaluate.py를 이어서 실행한다.
"""
import json

from baseline import (
    LOG_DIR,
    RESULTS_DIR,
    RUNS_DIR,
    build_parser,
    build_tasks,
    repeats_for,
    run_baseline_task,
)
from verifier import run_verified_task


def run_one(args, setting, task, repeat_idx):
    """설정에 맞는 실행 경로로 분기한다. C는 verifier, 그 외는 baseline."""
    if setting == "C":
        return run_verified_task(args, setting, task, repeat_idx)
    return run_baseline_task(args, setting, task, repeat_idx)


def main():
    args = build_parser().parse_args()
    LOG_DIR.mkdir(exist_ok=True)
    RUNS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    tasks = build_tasks()
    repeats = repeats_for(args.quick)
    expected_runs = sum(repeats[t["type"]] for t in tasks) * 3
    done = 0
    for setting in ["A", "B", "C"]:
        for task in tasks:
            for repeat_idx in range(1, repeats[task["type"]] + 1):
                result = run_one(args, setting, task, repeat_idx)
                out = LOG_DIR / f"{setting}_{task['id']}_{repeat_idx:02d}.json"
                out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
                done += 1
                print(f"[{done}/{expected_runs}] {setting} {task['id']} r{repeat_idx} success={result['success']} attempts={result['attempts']}")


if __name__ == "__main__":
    main()
