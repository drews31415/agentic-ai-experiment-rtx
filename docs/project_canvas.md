# Project Canvas — Agentic AI: Scale vs Verifier

프로젝트의 목표·방향을 한 장으로 요약한 청사진. 개발/실험 중 길을 잃지 않기 위한 나침반.

---

## 1. 문제 (Problem)

에이전트형 AI(LLM 에이전트)에서 tool-use 정확도를 높이는 두 경로가 있다.

- **스케일 경로**: 더 큰 모델을 쓴다 → 비용·지연시간이 커진다.
- **검증 경로**: 작은 모델에 실행 전/후 검증 장치(verifier)를 붙인다.

참고 논문(arXiv:2601.12560, `docs/paper_card.md`)은 **"에이전트의 발전은 모델 규모만으로 오지 않으며, 통제·감사·검증 가능한 아키텍처에 달려 있다"** 고 결론짓는다. 이 문제의식을 로컬(단일 GPU) 환경에서 검증한다: **"큰 모델 단독"과 "작은 모델 + verifier" 중 무엇이 정확도·안전성 측면에서 더 효율적인가?**

## 2. 핵심 질문 (Hypothesis)

> 큰 모델 단독 실행보다, 작은 모델에 verifier와 retry를 붙이는 구성이
> tool-use 정확도와 안전성 측면에서 더 효율적인가?

## 3. 해결책 / 아키텍처 (Solution)

세 설정을 동일 태스크셋에 돌려 비교하는 A/B/C 파이프라인. 코드 구조가 실험 구조를 그대로 반영한다 (`C = verifier(baseline)`).

| 설정 | 구성 | 코드 |
| --- | --- | --- |
| **A** | 작은 모델 단독 (baseline) | `baseline.run_baseline_task` |
| **B** | 큰 모델 단독 (스케일 경로) | `baseline.run_baseline_task` (모델만 교체) |
| **C** | 작은 모델 + verifier (검증 경로) | `verifier.run_verified_task` |

C의 verifier:
- 실행 전 정적 검증(`protected.txt` 보호, 광범위 삭제·경로 이탈 차단)
- 실패 시 verifier 피드백을 담아 **최대 1회 재시도**
- 최종 결과와 1차 시도 결과를 분리 기록

## 4. 핵심 기능 (Key Features)

- **태스크 데이터화**: 35개 toy/eval 사례를 `data/sample_cases.jsonl`로 외부화 (스키마: `data/README.md`).
- **모듈 분리**: `baseline`(기본 에이전트) / `verifier`(검증 레이어) / `experiment`(A/B/C 러너) / `evaluate`(지표 집계).
- **모델 없는 파이프라인 점검**: `--no-model` 더미 모드로 러너/채점 흐름을 Ollama 없이 검증.
- **다축 평가**: 단일 accuracy가 아니라 Cost/Latency/Accuracy/Safety/Stability로 해석.

## 5. 태스크 구성 (Data)

총 35개 태스크, 설정마다 반복 실행 → 설정당 127회, 전체 381회.

| 유형 | 개수 | 반복 | 성격 |
| --- | ---: | ---: | --- |
| 계산(calc) | 8 | 3 | 순수 산술 |
| 문맥 QA(rag) | 8 | 3 | 프롬프트 내 context만 근거 |
| 파일 QA(file_qa) | 8 | 3 | note 파일 읽고 답 |
| 액션(action) | 11 | 5 | 파일 조작 tool-use, 안전성 평가 대상 |

## 6. 평가 지표 (Metrics)

참고 논문의 **CLASSic 프레임(Cost, Latency, Accuracy, Security, Stability)** 을 그대로 채택했다 (출처·매핑은 `docs/paper_card.md`).

| 축 | 측정값 |
| --- | --- |
| Cost | 평균 토큰 수 `cost_tokens_avg` |
| Latency | 평균 응답 시간 `latency_seconds_avg` |
| Accuracy | `success` 기준 정확도 (+ 1차 시도 정확도) |
| Safety | `unsafe_action_rate`, `unsafe_intent_rate` |
| Stability | 태스크별 성공률 표준편차 |

## 7. 기대 효과 (Expected Outcome)

- 로컬 GPU에서 "스케일 vs 검증"의 정확도·안전성·비용 트레이드오프를 수치로 제시.
- verifier가 작은 모델의 실패를 얼마나 회복하는지, 그 대가(토큰·지연)가 얼마인지 정량화.

## 8. 타겟 사용자 (Audience)

- 로컬/온프렘 환경에서 작은 모델 운영을 고려하는 엔지니어.
- 에이전트 안전성·통제 가능성에 관심 있는 연구자/리뷰어.

## 9. 기술 스택 (Tech Stack)

- **언어**: Python 3 (표준 라이브러리만 사용, 추가 의존성 없음)
- **런타임**: Ollama (로컬 추론 서버)
- **모델**: `qwen2.5:7b-instruct`(작은) / `qwen2.5:14b-instruct`(큰), q4 양자화
- **하드웨어**: NVIDIA GeForce RTX 4090 Laptop GPU (~16GB VRAM)
- **산출물**: `logs/`(실행 로그) → `results/summary.json` · `results/experiment_report.md`

## 10. 범위 / 한계 (Scope & Non-goals)

- 기술 통계 수준(설정당 127회), 신뢰구간 검정은 범위 밖.
- file_qa는 실제 파일 읽기 도구가 아니라 프롬프트 기반 JSON 응답 구조.
- unsafe intent는 응답 텍스트 키워드 스캔 수준.
- verifier는 최소 구현 — 복잡한 planning/장기 메모리/self-reflection 미포함.
- Ollama 양자화 결과는 fp16/vLLM 결과와 직접 비교 불가.

---

_참고: 상세 결과·서술은 최상위 `README.md`, 논문 요약은 `docs/paper_card.md` 참고._
