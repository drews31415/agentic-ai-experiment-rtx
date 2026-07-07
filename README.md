# Agentic AI: Scale vs Verifier 비교 실험

이 레포는 에이전트형 AI에서 두 개선 경로를 비교하기 위한 로컬 재현 실험이다.

- 모델 스케일을 키우는 방법
- 작은 모델에 실행 전/후 검증 장치(verifier)를 붙이는 방법

참고 논문은 *Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents* 이다. 논문은 에이전트형 AI에서 모델 성능뿐 아니라 통제 가능성, 안전성, 감사 가능성이 중요하다는 방향을 제시한다. 이 실험은 그 문제의식을 바탕으로 다음 질문을 로컬 환경에서 확인한다.

> 큰 모델 단독 실행보다, 작은 모델에 verifier와 retry를 붙이는 구성이 tool-use 정확도와 안전성 측면에서 더 효율적인가?

## 현재 로컬 실행 조건

이 작업 디렉터리는 처음에 비어 있었기 때문에, 원본 실험 코드를 그대로 실행한 것이 아니라 같은 취지의 A/B/C 비교 파이프라인을 새로 구성해 실행했다.

| 항목 | 값 |
| --- | --- |
| 실행 날짜 | 2026-07-07 |
| 실행 장비 | NVIDIA GeForce RTX 4090 Laptop GPU, 약 16GB VRAM |
| 런타임 | Ollama |
| 작은 모델 | `qwen2.5:7b-instruct-q4_K_M` |
| 큰 모델 | `qwen2.5:14b-instruct-q4_K_M` |
| 실행 방식 | 단일 로컬 GPU, q4 양자화 모델 |
| 총 실행 수 | 381 |


## 실험 매트릭스

| 설정 | 구성 | 설명 |
| --- | --- | --- |
| A | 7B, no verifier | 작은 모델 단독 실행 |
| B | 14B, no verifier | 큰 모델 단독 실행 |
| C | 7B + verifier | 작은 모델에 실행 전 검증, 실행 후 채점, 최대 1회 재시도 적용 |

C의 verifier는 다음을 수행한다.

- `protected.txt` 수정/삭제 차단
- 광범위 삭제 및 경로 이탈 차단
- 실패 시 verifier feedback을 포함해 최대 1회 재시도
- 최종 결과와 1차 시도 결과를 분리 기록

## 태스크 구성

총 35개 태스크를 사용했다.

| 유형 | 개수 | 반복 |
| --- | ---: | ---: |
| 계산 | 8 | 3회 |
| RAG형 문맥 QA | 8 | 3회 |
| 파일 읽기 QA | 8 | 3회 |
| 액션/tool-use | 11 | 5회 |

세 설정 A/B/C에 대해 모두 실행하므로 전체 실행 수는 381회다.

## 평가 지표

결과는 단일 accuracy가 아니라 다음 축으로 해석한다.

| 축 | 측정값 |
| --- | --- |
| Cost | 평균 토큰 수, `cost_tokens_avg` |
| Latency | 평균 응답 시간, `latency_seconds_avg` |
| Accuracy | `success` 기준 정확도 |
| Safety | `unsafe_action_rate`, `unsafe_intent_rate` |
| Stability | 태스크별 성공률 표준편차 |

## 이번 로컬 실행 결과

집계 결과는 `results/summary.json`과 `results/experiment_report.md`에 저장되어 있다.

| 설정 | 실행 수 | 정확도 | 1차 시도 정확도 | unsafe action | unsafe intent | 평균 토큰 | 평균 지연시간(초) | 안정성 표준편차 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 127 | 0.6378 | 0.6378 | 0.0000 | 0.0000 | 162.77 | 3.00 | 0.4897 |
| B | 127 | 0.6850 | 0.6850 | 0.0000 | 0.0787 | 151.56 | 4.48 | 0.4799 |
| C | 127 | 0.6929 | 0.6378 | 0.0000 | 0.0000 | 225.45 | 5.51 | 0.4832 |

이번 로컬 실행에서는 C가 A보다 최종 정확도가 높았고, 1차 시도 정확도는 A와 동일했다. 즉 verifier가 기본 모델 능력 자체를 바꾼 것이 아니라 실패한 실행을 일부 재시도로 회복한 형태다.

B는 A보다 정확도가 높았지만 unsafe intent 탐지율이 0.0787로 나타났다. 실제 파일 시스템 위반인 `unsafe_action_rate`는 A/B/C 모두 0.0이었다.

C는 B보다 정확도가 약간 높고 unsafe intent는 낮았지만, verifier와 재시도 때문에 평균 토큰과 지연시간이 가장 높았다. 따라서 이 로컬 실행의 결론은 "verifier가 항상 더 싸고 빠르다"가 아니라, "verifier가 작은 모델의 실패 일부를 회복할 수 있지만 운영 비용과 지연시간을 증가시킬 수 있다"에 가깝다.

## 실행 방법

Ollama가 설치되어 있고 다음 모델이 내려받아져 있어야 한다.

```powershell
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
```

전체 실험 실행:

```powershell
python run_experiment.py --ollama-url http://localhost:11434 --small-model qwen2.5:7b-instruct-q4_K_M --large-model qwen2.5:14b-instruct-q4_K_M
python results/aggregate.py
```

빠른 파이프라인 점검:

```powershell
python run_experiment.py --quick
python results/aggregate.py
```

모델 호출 없이 러너/채점 파이프라인만 점검:

```powershell
python run_experiment.py --quick --no-model
python results/aggregate.py
```

## Repository 구조

| 경로 | 역할 |
| --- | --- |
| `run_experiment.py` | 태스크 생성, 모델 호출, verifier, 액션 실행, 로그 저장 |
| `logs/` | 381개 실행 로그 |
| `results/aggregate.py` | 로그 집계 스크립트 |
| `results/summary.json` | machine-readable 집계 결과 |
| `results/experiment_report.md` | 표 형태의 결과 보고서 |
| `runs/` | 액션 태스크별 임시 작업 디렉터리 |

## 한계

- 표본 크기는 설정당 127회이며, 신뢰구간 검정이 아니라 기술 통계다.
- 파일 QA 태스크는 실제 파일 읽기 도구를 모델에 제공한 구조가 아니라 프롬프트 기반 JSON 응답 구조다.
- unsafe intent 탐지는 raw 응답 텍스트에 대한 단순 키워드 스캔이다.
- Ollama 양자화 모델 결과는 fp16/vLLM 결과와 직접 비교하면 안 된다.
- verifier는 최소 구현이며, 복잡한 planning, 장기 메모리, self-reflection 구조는 포함하지 않았다.

## 결론

이번 로컬 실행에서는 verifier를 붙인 C가 A보다 높은 최종 정확도를 보였고, 1차 시도 정확도는 A와 같았다. 이는 verifier가 작은 모델의 기본 추론 능력을 직접 향상시키기보다는 실패한 실행을 감지하고 일부 회복하는 안전망으로 작동했음을 보여준다.

다만 C는 평균 토큰과 지연시간이 가장 높았다. 따라서 이 환경에서의 실용적 결론은 다음과 같다.

> 작은 모델 + verifier는 실행 실패를 일부 회복할 수 있지만, 그 이득은 추가 토큰 비용과 지연시간을 함께 평가해야 한다.
