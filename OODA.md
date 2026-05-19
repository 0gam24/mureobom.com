# OODA.md — 물어봄 의사결정 루프

> Observe → Orient → Decide → Act → (피드백) → Observe 다음 사이클.
> 본 문서는 mureobom 운영에 발생하는 모든 의사결정을 **3개 층위(Macro/Micro/Agent)**의
> OODA 루프로 명시한다. 어느 회의·결정이 어느 루프에 속하는지 분명히 해서,
> "감으로" 또는 "임시방편으로" 룰을 갈아끼우는 일을 막는 게 목적.

---

## 층위 한 줄 요약

| 층위 | 주기 | 누가 | 산출 |
|---|---|---|---|
| **Macro** (프로젝트) | 주 1회 + 월 1회 | 운영자 + Claude | [decisions.log.md](automation/ooda/decisions.log.md) 엔트리, scoring.yaml/seed/compliance PR |
| **Micro** (브리프 검수) | 브리프 1건당 ~15분 | 사람 검수자 | brief.yaml `status: approved` + `차별화:` 라인 |
| **Agent** (에이전트 1회 실행) | 호출당 자동 | Claude 서브에이전트 | 각 에이전트 출력 (brief 초안 / research bundle / draft / FAQ / 통과·차단) |

각 층위의 피드백은 **다음 상위 층위의 Observe**로 흘러야 한다.
(Agent 차단 통계 → Macro의 compliance 룰 갱신 / Micro 발행 후 traffic → Macro의 scoring 가중치).

---

## 1. Macro OODA — 프로젝트 운영 (주간 + 월간)

### Observe (수집)
운영자가 [automation/ooda/observations.template.md](automation/ooda/observations.template.md)
복사해서 주별 스냅샷 작성. 측정 대상:

| 카테고리 | 메트릭 | 출처 |
|---|---|---|
| 트래픽 | 클릭·노출·평균 게재순위·CTR (쿼리·페이지별) | Google Search Console |
| 트래픽 | 네이버 유입·체류 | Naver Search Advisor |
| 수익 | RPM·eCPM·CTR·노출수·차단률 | AdSense 보고서 |
| 발행 | 신규 글 수, 브리프 승인률, 큐 대기 N | `automation/briefs/_published_slugs.txt` + `topic-queue.json` |
| 품질 | compliance 차단 빈도 (룰 ID별), 평균 본문 길이, FAQ 평균 개수 | PR 코멘트 grep |
| 운영 | NAVER API 호출량, 워크플로 실패 수 | `automation/_stats.json` (Phase 3에서 생성) |
| 색인 | 색인 완료 페이지 / 발행 페이지 비율 | Search Console + Naver SA |

### Orient (해석)
원자료를 다음 질문에 매핑:

1. 어느 **클러스터·키워드**가 트래픽 견인? (롱테일 vs 헤드)
2. 어느 **compliance 룰**이 차단 1위? (룰이 강한 건가, 글이 약한 건가)
3. **유사문서 차단**(O-04) 빈도가 늘면 차별화 룰이 안 먹는다는 신호
4. **API 한도** 압박? (실측 vs 예상 80회/일)
5. **AdSense RPM**이 어느 클러스터에서 높은가? (loan/insurance 통상 高)
6. **색인 미완료** 페이지가 누적되면 sitemap·canonical·내부링크 문제 의심
7. **postdate 폴백 분포** — 위치 프록시 비중이 점점 커지면 kin API 응답 형식 변화 의심

### Decide (결정)
가능한 조치 옵션 (해석 결과별):

| 신호 | 조치 후보 |
|---|---|
| 특정 시드만 점수 폭주, 다른 시드 0 | [seed-keywords.yaml](automation/config/seed-keywords.yaml) 시드 재편 (분할·통합) |
| 트렌드 가중치가 freshness보다 너무 셈 | [scoring.yaml](automation/config/scoring.yaml) 가중치 v2 (트렌드↓ / fit↑) |
| 동일 룰 ID 차단 ≥30%/주 | [compliance/checklist.md](compliance/checklist.md) 해당 룰 정밀화 또는 경고로 격하 |
| 유사문서 차단↑ | brief-generator의 `차별화:` 가이드 강화 + 시드에서 과포화 키워드 제거 |
| API 한도 70% 도달 | 캐싱 도입 (CLAUDE.md 함정 섹션) |
| AdSense 정책 변경 | AD-* 룰 갱신, 슬롯 위치 재배치 |
| 색인 미완 페이지 누적 | 내부링크 보강(geo 에이전트 강화) + 수동 색인 요청 |

**모든 결정은 [decisions.log.md](automation/ooda/decisions.log.md)에 한 항목씩 기록.**
"왜 이 결정을 했는지"는 6개월 후 재평가 때 필수 컨텍스트.

### Act (실행)
- 설정 변경은 단일 PR로 ("ooda-week-{YYYY-WW}" 브랜치 권장).
- PR 본문 = decisions.log.md 엔트리 링크.
- 머지 즉시 효과 측정 시작.

### Feedback (피드백)
- 1주: 직전 결정의 즉시 효과 (e.g., 가중치 변경 후 큐 다양성↑)
- 1개월: 누적 효과 (e.g., 차별화 가이드 강화 후 O-04 차단률↓)
- 결정과 결과를 같은 로그 항목의 "Outcome" 섹션에 추적

---

## 2. Micro OODA — 브리프 검수 (사람, 15분/건)

검수자가 brief 1건에 대해 반복하는 루프. **Macro Observe로 누적될 메트릭의 1차 결정**.

### Observe
- `signal.score` 와 컴포넌트 (trend_momentum / question_volume / cluster_fit / freshness)
- `target_query` 자연어
- `must_cover` 항목들 (충분히 사실 단위인가?)
- 기존 발행 슬러그 (`automation/briefs/_published_slugs.txt`)와 의미 중복 여부

### Orient
- 이 토픽을 **네이버 블로그·다른 Q&A가 어떻게 다루는지** 1분 그레프
- 우리만의 **차별화 각도**가 분명한가? (예: 2026 신규 케이스, 권고사직 vs 자발 위장 구분 표)
- `must_cover`에서 **빠진 핵심**이 있는가?
- 인텐트 추정이 자연스러운가? (정보형/절차형/거래형)

### Decide
4지선다:

1. **approve** — 차별화 각도가 분명하면 `human_notes` 첫 줄 `차별화: {각도}` 채우고 `status: approved`
2. **send-back to draft** — must_cover 보강 필요. 검수자가 직접 보완 후 approve
3. **merge with existing** — 이미 발행된 글 갱신이 더 적절. 큐에서 제거 + 발행 글 `updated` 갱신 큐로 이동
4. **reject** — 차별화 불가능 / 우리 4 클러스터 밖. 큐에서 제거 + 사유 기록 (다음 주기 시드 정리 input)

### Act
- approve 시: brief 파일 저장 → 무인 파이프라인 자동 진입
- reject 시: 큐 항목에 `rejected: {사유}` 한 줄 추가하여 다음 스캐너가 재제안 안 하도록

### Feedback
- 통과율 (compliance OK / 발행 차단) — Macro에 누적
- 발행 후 1주 traffic — Macro의 클러스터 성과 데이터
- 차별화 각도가 실제 D.I.A.+ 페널티를 피했는지 (유사문서 차단률)

---

## 3. Agent OODA — 5 파이프라인 에이전트

각 서브에이전트 정의 자체가 OODA를 implicit하게 따른다. 명시적 재구조 불필요.
다만 **Decide↔Act 경계가 명확해야 함**:

| 에이전트 | Observe | Orient | Decide | Act |
|---|---|---|---|---|
| brief-generator | queue 항목 + seed | 클러스터 fit + 중복 | draft 작성 vs 거부 | brief.yaml write |
| researcher | approved brief | 화이트리스트 도메인 매칭 | 어느 URL 패치 | bundle.json write |
| writer | brief + bundle | must_cover 매핑 + 어조 | 본문 구조 | answers/{slug}.md write |
| geo | draft md | FAQ·llms 갱신 필요성 | Q/A 짝 + llms 라인 | frontmatter 갱신 + llms.txt |
| compliance | 최종 본문 | 룰 매트릭스 적용 | pass / block / warn | status flip + 라벨 부여 |

**규칙**: 어느 에이전트도 자기 단계 밖의 결정을 하지 않는다. 예) writer가
compliance 우회를 위해 본문을 미리 수정하면 안 됨. brief-generator가
researcher의 출처 화이트리스트를 미리 호출하지 않음.

각 에이전트의 산출은 **다음 단계의 Observe**가 된다 — 깨끗한 핸드오프가 OODA의 핵심.

---

## 운영 캐던스 한 줄

- **매일 KST 06:00**: cron 스캐너 (Macro Observe의 일부)
- **매일**: 운영자 큐 검토 + N건 Micro OODA
- **주 1회 (월요일 09:00 권장)**: Macro OODA 1주차 — observations 작성 + decisions 1~3건
- **월 1회 (월말)**: Macro OODA 1개월 — 누적 추세 + 가중치 재튜닝 후보
- **분기 1회**: 시드·클러스터 IA 재검토

각 결정은 PR + decisions.log 항목 1개. 결정 없는 주는 "no change — outcomes 안정" 한 줄.

---

## OODA가 깨지는 신호 (자가진단)

- 결정 PR이 decisions.log 항목 없이 머지됨 → ADR 부재, 6개월 후 미스터리
- 같은 룰을 매주 반대로 토글 → Orient가 약함, 메트릭 더 모아야
- compliance 차단률 변동을 매주 보지만 Act 없음 → "관찰만 하고 끝나는" 마비
- 운영자가 Micro 단계에서 차별화 라인을 비우고 approve → Macro 메트릭 오염
- 에이전트가 자기 단계 밖 결정 (writer가 compliance 우회) → 핸드오프 오염

위 신호가 보이면 본 OODA.md를 다시 읽고 책임 층위를 명확히 하라.
