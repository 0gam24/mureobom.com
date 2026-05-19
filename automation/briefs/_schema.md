# brief.yaml 스키마 — 물어봄

사람이 약 15분 검수/보완하는 단 하나의 수작업 산출물.
이 파일이 승인(`status: approved`)되면 이후 리서치·작성·GEO·검수·발행이 무인으로 진행된다.

검수자 의사결정 프로토콜: [OODA.md §2 Micro OODA](../../OODA.md) — Observe(점수/시그널) →
Orient(차별화 가능 각도) → Decide(approve/send-back/merge/reject) → Act(status 변경).

## 필드 정의

| 필드 | 필수 | 설명 |
|---|---|---|
| `id` | ✔ | 고유 ID (`{cluster}-{slug}`) |
| `cluster` | ✔ | tax / support / loan / insurance |
| `status` | ✔ | `draft` → `approved` → `published` |
| `target_query` | ✔ | 이 글이 잡을 핵심 검색 질의(사람 손질) |
| `search_intent` | ✔ | 정보형 / 거래형 / 절차형 등 사용자 의도 |
| `signal` | ✔ | 스캐너 산출 점수·시그널(읽기용, 원문 아님) |
| `must_cover` | ✔ | 반드시 다룰 핵심 포인트 목록 |
| `required_sources` | ✔ | 공식 1차 출처(법령·기관). 0건이면 발행 차단 |
| `internal_links` | ✖ | 같은/다른 클러스터 연결 슬러그 |
| `compliance` | ✔ | 금융 표현 가드·일반정보 고지 플래그 (구 KFTC/FSS 키는 폐기) |
| `geo` | ✖ | FAQ 스키마용 Q/A 쌍, llms.txt 반영 여부 |
| `human_notes` | ✔ | 검수자 메모. **첫 줄은 반드시 `차별화: {각도}`** (네이버 D.I.A.+ 유사문서 회피) |

## 폐기된 필드 (사용 금지)

- ~~`cta`~~ — calculatorhost 딥링크·제휴 CTA 폐기. 수익화는 AdSense 단독.
  brief에 적어도 무시되고 frontmatter에 옮겨지지 않는다.
- ~~`compliance.kftc_disclosure`, `compliance.fss_ad_review`~~ — 제휴 표시
  의무 폐기와 함께 제거. `compliance.medical_legal_financial_advice_disclaimer`
  (= disclaimer 플래그)만 유지.

## 금지

- 지식iN 질문/답변 원문, 캡처, 장문 인용 금지.
- `signal`에는 집계 수치만. 개별 질문 문장 복붙 금지.
- 외부 도구·계산기·제휴 URL 명시 금지 (writer가 본문에 끌어쓰지 못하도록).
