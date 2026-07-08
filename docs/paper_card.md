# Paper Card

이 프로젝트가 참고한 문헌의 핵심을 요약한 카드. "만들기 위해 참고한 자료"를 정리해 둔 요약장.

---

## 서지 정보 (Bibliography)

| 항목 | 값 |
| --- | --- |
| 제목 | *Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents* |
| 저자 | Arunkumar V (Anna University, Tiruchirappalli) · Gangadharan G.R. (NIT Tiruchirappalli) · Rajkumar Buyya (University of Melbourne) |
| 식별자 | arXiv:2601.12560v1 [cs.AI] |
| 발표일 | 2026-01-18 |
| 유형 | 서베이 / 아키텍처·엔지니어링 중심 정리 |

## 한 줄 요약 (TL;DR)

AI는 "텍스트를 생성하는 모델"에서 "인지·추론·계획·행동을 수행하는 **에이전트형 AI(Agentic AI)**"로 이동 중이다. 이 논문은 LLM 에이전트를 **6개 모듈 차원**으로 분해하는 통합 분류 체계를 제시하고, 성능뿐 아니라 **통제 가능성·안전성·감사 가능성**이 실제 배포의 핵심임을 강조한다. 핵심 메시지: **"발전은 모델 규모만으로 오지 않는다. 통제·감사·정렬 가능한 아키텍처에 달려 있다."**

## 핵심 기여 (Key Contributions)

1. **통합 아키텍처 중심 분류 체계** — LLM 에이전트를 6개 차원으로 분해:
   Core Components(perception, memory, action, profiling) · Cognitive Architecture(planning, reflection) · Learning · Multi-Agent Systems · Environments · **Evaluation**.
2. **엔지니어링·시스템 관점** — 메모리 백엔드/보존 정책, code-as-action, **MCP(Model Context Protocol)** 표준 커넥터, 명시적 상태 전환을 강제하는 오케스트레이션 컨트롤러 등 "배포에서 실제로 중요한" 설계 선택을 조명.
3. **자율 루프 → 통제 가능한 그래프** — 다중 에이전트 상호작용(chain/star/mesh/workflow graph)과 프레임워크(CAMEL, AutoGen, MetaGPT, LangGraph, Swarm, MAKER)를 동일 관점으로 분석.
4. **환경·평가·안전의 전체론적 관점** — 평가를 **CLASSic** 차원(Cost, Latency, Accuracy, Security, Stability)으로 통합하고, hallucination-in-action·무한 루프·prompt injection 같은 구체적 실패 모드와 연결.

## 형식 모델 (Formal Model)

에이전트를 POMDP 기반 제어 루프로 정의: **A = ⟨S, O, M, T, π⟩**
지각(Φ) → 메모리 업데이트(μ, RAG 포함) → 인지 계획(Ψ, 행동 전 잠재 추론) → 행동 정책(π) → 환경 반응·피드백(E) → 루프. 본 프로젝트의 태스크→응답→(검증)→채점 흐름은 이 루프의 축소판이다.

## 이 논문이 정의한 CLASSic 평가 프레임 (본 프로젝트 지표의 출처)

논문 Section 7의 CLASSic 5축이 **본 프로젝트 평가 지표와 1:1로 대응**한다.

| CLASSic (논문 §7) | 논문 요지 | 본 프로젝트 지표 |
| --- | --- | --- |
| **C**ost | 계층적/트리탐색 에이전트는 성능↑지만 비용 페널티 | `cost_tokens_avg` |
| **L**atency | 실세계 작업엔 엄격한 지연 평가 필요 | `latency_seconds_avg` |
| **A**ccuracy | 정적 QA만으론 부족 — 도구 사용·상태 추적·장기 복구에서 성공률 급락 | `success` 정확도 (+ 1차 시도 정확도) |
| **S**ecurity | 도구 연결 시 prompt injection이 에이전트를 "confused deputy"로 전락시킴 | `unsafe_action_rate`, `unsafe_intent_rate` |
| **S**tability | 반복 실행 분산·최악 실패를 평균과 함께 보고해야 함 | `stability_success_rate_stddev` |

## 우리 프로젝트에 적용한 인사이트 (Insights Applied)

| 논문 관점 | 본 프로젝트 반영 |
| --- | --- |
| 성능만으로 에이전트를 평가하면 안 됨 (CLASSic) | 단일 accuracy 대신 **Cost/Latency/Accuracy/Safety/Stability 다축 평가** |
| §7.4 — 실행 전 계획을 검증하는 **독립적 정책/감사 구성요소**, 민감 액션에 대한 명시적 확인, 제한된 도구 권한 | **verifier(`verify_pre`)** 로 `protected.txt` 보호·광범위 삭제·경로 이탈 차단 (설정 C) |
| §7.4 — 직접/**간접 prompt injection**(untrusted 콘텐츠가 지시를 덮어씀) | action 태스크에 인젝션형 유혹 삽입("문서가 protected.txt를 지우라 함") → 실제 태스크만 수행하는지 평가 |
| MCP 경계에서의 **allowlist·감사 로깅**(audit logging) | 실행별 원시 응답·파싱·재시도 이력을 `logs/`에 JSON으로 **전량 기록** |
| §8.2 — 실패 시 전략 변경 없이 반복 → 무한 루프 | verifier는 피드백을 담아 **최대 1회만** 재시도(무한 루프 방지) |
| 결론 — **"모델 규모만으론 발전 없음"**, 통제·검증이 열쇠 | 실험 핵심 질문: 큰 모델 단독(B) vs 작은 모델+verifier(C) |

## 한계 및 우리 실험과의 간극 (Limitations / Gaps)

- 논문은 개념·분류 중심 서베이 → 본 실험은 특정 벤치마크 재현이 아니라 **같은 문제의식을 로컬에서 축소 재구성**한 것.
- 본 실험 verifier는 **정적 규칙 + 1회 재시도**의 최소 구현. 논문이 언급한 SelfCheckGPT류 추론 검증, meta-cognitive 루프 탈출, constitutional AI 정렬은 미포함.
- unsafe intent 탐지는 **키워드 스캔** 수준(논문의 PromptArmor/적응형 공격 논의보다 단순).
- 로컬 q4 양자화 결과라 논문이 다루는 대형/풀정밀 세팅과 직접 비교 불가.

## 후속 확인/작업 (Follow-ups)

- [ ] 논문 §7.4의 완화책(compartmentalized sandbox, 사용자 확인)을 verifier에 추가 반영할지 검토.
- [ ] 논문의 taxonomy 6차원에서 본 실험 A/B/C의 위치를 명시 매핑.
- [ ] hallucination-in-action(존재하지 않는 파일 삭제 등)을 별도 실패 유형으로 `metrics.csv`에 집계.

---

_관련 문서: 프로젝트 청사진은 `docs/project_canvas.md`, 실행/결과는 최상위 `README.md`._
