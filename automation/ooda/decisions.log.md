# Decisions Log — 물어봄 Macro OODA

> 운영자가 매주 Macro OODA에서 채택한 결정을 한 항목씩 시간 역순으로 기록.
> ADR(Architecture Decision Record) lite 형식. 결정마다 30초~2분 투자.
> 6개월 후 "이건 왜 이렇게 됐지?" 미스터리 방지가 목적.
>
> 양식: 새 항목은 **맨 위에** (역시간순). 항목 ID는 `D-{YYYY-MM-DD}-{N}`.

---

## 양식 (복사용)

```
## D-{YYYY-MM-DD}-{N}: {한 줄 결정 제목}

- **층위**: Macro 주간 / Macro 월간 / 긴급(즉시)
- **변경**: {파일·룰·가중치 1~3줄}
- **근거 (Orient)**: {observations/{YYYY-WW}.md 어느 섹션의 어느 수치}
- **기대 효과**:
  - 1주: {지표}
  - 1개월: {지표}
- **롤백 기준**: {N주 후 효과 없으면 revert}
- **연관 PR**: #{번호}
- **Outcome (1주 후 작성)**:
- **Outcome (1개월 후 작성)**:
```

---

## D-2026-07-20-1: 일일 발행 보류(4일 연속) — 클라우드 egress 차단 지속, 04:30 + 06:00 재시도 모두 실패

- **층위**: 긴급(즉시) — 발행 파이프라인 중단
- **변경**: 2026-07-20 KST **04:30 클라우드 런**이 3편(loan·tax·insurance) brief를
  즉석 승인(approved)까지 진행하고 egress 차단으로 본문 발행을 보류. 승인 brief만 커밋.
  스캐너 큐(topic-queue.json)가 stale(2026-06-11)이고 상위 항목이 전부 기발행이라
  사이트 공백을 메우는 3편을 수동 선정(의미중복 없음 확인):
  - loan/주택담보대출-방공제-mci-mcg-한도 (LTV와 별개로 한도를 깎는 방공제 + MCI/MCG 복원)
  - tax/폐업-부가가치세-확정신고-절차 (폐업 부가세 확정신고 → 잔존재화 간주공급 → 다음해 종소세)
  - insurance/기초연금-수급자격-소득인정액 (소득인정액·선정기준액 + 국민연금 연계 감액 오해 반박)
- **근거 (Orient)**: 04:30 런 실측 — `www.law.go.kr`·`www.nts.go.kr`·`www.moel.go.kr`·
  `www.nhis.or.kr` WebFetch/curl 초기 4회 + 60초 간격 재시도 3회 전부
  `CONNECT 403 / policy denial`(HTTP 000). 프록시 status `recentRelayFailures`도
  `connect_rejected / policy denial`로 law.go.kr·nts.go.kr·nhis.or.kr 기록.
  github push 경로만 열린 허용목록 정책 유지. researcher가 sources[].url을
  HTTP 200 + 실내용으로 검증 불가 → **절대 원칙 2 위반 회피 위해 발행 차단**.
  **06:00 재시도 런(이 항목 갱신)**: egress 복구만 재확인 → `www.law.go.kr`·
  `www.nts.go.kr`·`www.mohw.go.kr`·`www.hf.go.kr` 초기 CONNECT 4회 + 60초 간격
  재시도 3회(총 16 프로브) 전부 `CONNECT tunnel failed, response 403`(HTTP 000).
  프록시 status `recentRelayFailures` 비어 있으나 CONNECT 단계에서 정책 거부.
  차단 지속 확인 → 신규 brief 생성 안 함(중복 방지 §0), 보류 유지.
- **패턴 경보**: KST 07-17→07-18→07-19→07-20 **4일 연속** 클라우드 04:30 런이 egress로 보류.
  종전 3일은 이후 로컬(egress 허용) 런이 승인 brief를 소진해 정상 발행
  (07-18=`ef3de02`, 07-19=`690d98a`). 일시 장애 아닌 **고정 egress 정책 문제** 확정.
- **기대 효과 / 권고**:
  - 단기: 07-20 3편을 로컬 아침 인계 크론(08:07 KST) 또는 egress 허용 환경에서
    소진 발행(brief 이미 approved라 researcher부터 재개).
  - 근본: 클라우드 네트워크 정책에 law.go.kr·nts.go.kr·moel.go.kr·mohw.go.kr·
    nps.or.kr·hf.go.kr·fss.or.kr·fsc.go.kr 허용 추가를 운영자가 조정해야
    무인 클라우드 발행 재개 가능.
- **롤백 기준**: N/A (환경 제약).
- **연관 PR**: (이 커밋 — brief 승인 + ADR. 발행은 후속 로컬 런에서 소진).

---

## D-2026-07-19-1: 일일 발행 보류(3일 연속) — 클라우드 egress 차단 지속, 04:30 + 06:00 재시도 모두 실패

- **층위**: 긴급(즉시) — 발행 파이프라인 중단
- **변경**: 2026-07-19 KST 자동 발행. **04:30 런**이 3편 brief를 즉석 승인(approved)까지
  진행하고 egress 차단으로 본문 발행을 보류한 뒤 승인 brief만 커밋(`252ac72`).
  **06:00 재시도 런**(이 항목)은 egress 복구 여부만 재확인 → 여전히 차단이라
  추가 작업 없이 보류 유지. 신규 brief 생성 안 함(중복 방지, §0).
  - loan/전세-계약갱신청구권-전월세상한제
  - tax/생애최초-취득세-감면-조건-한도
  - support/노인맞춤돌봄서비스-신청자격-내용
- **근거 (Orient)**: 06:00 재시도 실측 — `www.law.go.kr` 60초 간격 3회 + `example.com`
  단발 프로브 전부 `CONNECT tunnel failed, response 403`(gateway policy denial).
  프록시 status의 `recentRelayFailures`도 `connect_rejected / policy denial`로
  law.go.kr·support.google.com·example.com 기록. 즉 특정 도메인이 아니라
  **아웃바운드 HTTPS 전면 차단**(허용목록에 github push 경로만 열림).
  researcher가 sources[].url을 HTTP 200 + 실내용으로 검증 불가 →
  **절대 원칙 2(공식 1차 출처 검증 필수)** 위반 회피 위해 발행 차단 유지.
- **패턴 경보**: KST 07-17→07-18→07-19 **3일 연속** 클라우드 04:30 런이 egress로 보류.
  종전 2일은 이후 로컬(egress 허용) 런이 승인 brief를 소진해 정상 발행(07-18분 = `ef3de02`).
  일시 장애가 아니라 이 클라우드 환경의 **고정 egress 정책 문제**로 판단.
- **기대 효과 / 권고**:
  - 단기: 07-19 3편을 로컬 또는 egress 허용 환경에서 소진 발행(brief 이미 approved라 researcher부터 재개).
  - 근본: 클라우드 환경 네트워크 정책에 gov.kr·law.go.kr·nts.go.kr·nps.or.kr·bok.or.kr·fss.or.kr
    허용 추가 여부를 운영자가 확인/조정해야 무인 클라우드 발행 재개 가능.
- **롤백 기준**: N/A (환경 제약).
- **연관 PR**: (이 커밋 — decisions.log ADR 보강만. brief 승인·발행 보류는 `252ac72`)

---

## D-2026-07-18-1: 일일 발행 보류 — 클라우드 egress 정책이 공식 1차 출처 도메인 차단

- **층위**: 긴급(즉시) — 발행 파이프라인 중단
- **변경**: 2026-07-18 KST 자동 발행 런에서 3편(loan·tax·insurance) brief를
  즉석 승인(approved)까지 진행했으나, **본문 발행은 보류**하고 승인 brief만 커밋.
  - loan/전월세전환율-계산-법정한도
  - tax/부가가치세-조기환급-대상-신청-기간
  - insurance/국민연금-출산크레딧-군복무크레딧-가입기간
- **근거 (Orient)**: 이 클라우드 세션의 egress 정책 프록시가 공식 1차 출처
  도메인을 CONNECT 403(policy denial)로 전면 차단. 실측(재시도 포함):
  `www.law.go.kr`·`www.nts.go.kr`·`www.nps.or.kr`·`www.bok.or.kr` 전부
  `connect_rejected / policy denial`. `raw.githubusercontent.com`은 200
  (그래서 github push는 정상) — 즉 광범위 웹 차단 + 허용목록 정책.
  researcher가 sources[].url을 HTTP 200으로 검증 불가 →
  **절대 원칙 2(공식 1차 출처 검증 필수)** 위반을 피하기 위해 발행 차단.
- **기대 효과**: 다음 런(로컬 또는 egress 허용 환경)에서 이 3개 승인 brief를
  소진해 정상 발행. brief는 이미 승인 상태라 researcher부터 재개 가능.
- **롤백 기준**: N/A (환경 제약). egress 정책에 gov.kr/law.go.kr/nts.go.kr/
  nps.or.kr/bok.or.kr 허용이 추가되면 클라우드 런 재개.
- **연관 PR**: (이 커밋 — 브리프 승인만, 발행 보류)

---

## D-2026-06-15-1: 토픽 엔진 — 스캐너 큐 주도 발행 + 파생 질의/의미중복 차단

- **층위**: 긴급(즉시) — 토픽 소스 구조 변경
- **변경**:
  - `topic_scanner.py`: (1) `is_covered()` 의미중복 차단 — `_published_slugs.txt`에
    대해 같은 클러스터 내 부분문자열 매칭으로 시드형 후보 하드 스킵(구 정확매칭
    `dup_penalty` 폐기). (2) `derive_queries()` 롱테일 파생 질의 마이닝 — kin 제목
    N-gram(≥2회) → `{시드} {토큰}` 후보 + 자체 kin_search 신호. (3) `cluster_fit_boost`
    실제 적용(loan 1.15 / tax 1.10).
  - `scoring.yaml`: `max_derived_per_seed: 3` 추가, dup_penalty 주석 정리.
  - `publish-daily` 스킬: 토픽 소스 우선순위를 **큐 1차 / 캘린더 폴백**으로 전환.
- **근거 (Orient)**: 직전 `topic-queue.json` 20개 키워드가 `_published_slugs.txt`와
  대조 시 12개가 의미중복(시드형 슬러그가 구체 발행 슬러그의 부분문자열) — 정확매칭
  dedup이 전부 놓쳐 "죽은 큐". 캘린더(6/25 소진)는 한시적이라 지속 토픽 엔진 부재.
- **기대 효과**:
  - 1주: 큐에 기발행과 다른 신규 롱테일 ≥60% 비중. 발행 KILL(중복) 0건.
  - 1개월: 캘린더 의존 없이 스캐너 큐만으로 일 3편 지속 가능.
- **롤백 기준**: 파생 질의 품질이 낮아 brief 거부율 >50%면 `max_derived_per_seed`
  하향 또는 파생 마이닝 비활성, 캘린더 폴백 복귀.
- **연관 PR**: (이번 커밋)
- **지식iN 가드**: 제목 원문 미보관, 토큰 빈도 집계만 — 절대 원칙 1 유지.
- **Outcome (1주 후 작성)**:
- **Outcome (1개월 후 작성)**:

## D-2026-06-11-3: 발행 캐던스 — loan·tax 매일 고정 1편씩 + support/insurance 격일 교대

- **층위**: Macro 주간
- **변경**: 일일 3편 기준 클러스터 배분을 `loan 1 + tax 1 + (support/insurance 교대 1)`로
  고정. [scoring.yaml](../config/scoring.yaml)에 `cluster_fit_boost`(loan 1.15 / tax 1.10)
  추가, [publish-daily 스킬](../../.claude/skills/publish-daily/SKILL.md) §2에 배분 규칙 인코딩.
- **근거 (Orient)**: 금융(대출)·세금 키워드는 AdSense RPM이 지원금·보험 대비 높은
  대표 고단가 버티컬. 발행 85편 시점에서 코퍼스가 4클러스터 균등 — 수익 가중 없이
  순환만 하면 단가 낮은 글 비중이 그대로 유지됨.
- **기대 효과**:
  - 1주: 신규 발행의 loan+tax 비중 ≥ 66%
  - 1개월: AdSense 페이지 RPM에서 loan·tax 글 우위 실측 → 계수 재튜닝 근거 확보
- **롤백 기준**: 1개월 후 GA4·AdSense 실측에서 loan·tax RPM 우위가 없으면 균등 배분 복귀
- **연관 PR**: (하네스 일괄)
- **Outcome (1주 후 작성)**:
- **Outcome (1개월 후 작성)**:

---

## D-2026-06-11-2: CMP는 AdSense 콘솔 GDPR 기본 메시지로 — 코드 변경 없음

- **층위**: Macro 주간
- **변경**: GDPR/EEA 동의 관리(CMP)는 자체 구현하지 않고 AdSense 콘솔
  Privacy & messaging의 Google 인증 기본 메시지를 게시하는 것으로 확정.
  [WORKFLOW.md](../../WORKFLOW.md) §6.5 "승인 직후 (D-Day)" 체크리스트 ③에 인코딩.
- **근거 (Orient)**: 트래픽의 EEA 비중이 사실상 0인 한국어 사이트에서 자체 CMP
  코드는 유지보수 비용만 추가. Google 인증 CMP 요건은 콘솔 메시지 게시로 충족됨.
- **기대 효과**:
  - 1주: AdSense 승인 직후 15분 체크리스트 안에서 처리 완료 (별도 PR 0건)
  - 1개월: EEA 트래픽 발생 시에도 광고 제한 경고 없음
- **롤백 기준**: EEA 트래픽 비중 5% 초과 + 동의율 문제 발생 시 자체 CMP 재검토
- **연관 PR**: 없음 (콘솔 작업)
- **Outcome (1주 후 작성)**:
- **Outcome (1개월 후 작성)**:

---

## D-2026-06-11-1: mid 광고 슬롯은 보류 — 7천자+ 장문 글 30% 초과 시 재검토

- **층위**: Macro 주간
- **변경**: 광고 슬롯은 현행 top/bottom 2개 유지. 본문 중간(mid) 슬롯은
  "공백 제외 7,000자 이상 장문 글이 전체 발행 글의 30%를 초과"하는 시점에
  도입을 검토하는 트리거 조건만 기록 (지금 코드 변경 없음).
- **근거 (Orient)**: 현 평균 본문 분량에서 mid 슬롯은 광고 밀도만 높여 AdSense
  정책 리스크(콘텐츠 대비 광고 과다)와 출처 박스 인접 금지(AD-04) 충돌 위험.
  장문 비중이 커져야 본문 중간 휴식 지점이 자연스럽게 생김.
- **기대 효과**:
  - 1주: 없음 (트리거 조건 기록만)
  - 1개월: 월간 OODA에서 7천자+ 글 비중 1줄 측정 → 트리거 도달 여부 판단
- **롤백 기준**: 해당 없음 (도입 보류 결정 — 트리거 도달 시 별도 결정으로 진행)
- **연관 PR**: 없음
- **Outcome (1주 후 작성)**:
- **Outcome (1개월 후 작성)**:

---

## D-2026-05-20-2: W22 종료까지 외부 채널 3종 연결 데드라인

- **층위**: Macro 주간
- **변경**: GSC / Naver SA / AdSense 사이트 승인 — W22 종료(2026-05-31)까지 ≥2 연결.
  미달 시 OODA 캐던스를 격주로 늦춤 (현실 인정 모드).
- **근거 (Orient)**: [observations/2026-W21.md](observations/2026-W21.md) §7 —
  외부 채널 3종 모두 미연결로 Macro Observe §2·§3·§4 전체가 공란. 이 상태가 1주 더
  지속되면 OODA.md §"OODA가 깨지는 신호" 중 "관찰만 하고 끝나는 마비" 신호 발동.
- **기대 효과**:
  - 1주: 3채널 중 ≥2 연결 완료
  - 1개월: GSC 색인 페이지 / 발행 페이지 비율 측정 가능
- **롤백 기준**: W22 종료에도 0개 연결이면 주간 캐던스 → 격주로 변경
- **연관 PR**: 없음 (외부 작업)
- **Outcome (1주 후 작성)**: (대기 — 2026-05-27)
- **Outcome (1개월 후 작성)**: (대기 — 2026-06-20)

---

## D-2026-05-20-1: topic_scanner 가동으로 큐 stale 해소

- **층위**: Macro 주간
- **변경**: `topic-queue.json`(현재 stale 1건) 리셋 후 [topic_scanner.py](../scripts/topic_scanner.py)
  1회 수동 가동. 결과로 Micro OODA의 정상 큐 기반 사이클 진입.
- **근거 (Orient)**: [observations/2026-W21.md](observations/2026-W21.md) §1 —
  큐 1건이 이미 발행된 4대보험 항목. 스캐너 미가동 상태로는 다음 주차도 동일 상태 유지.
- **기대 효과**:
  - 1주: 큐 ≥ 5건 신규 토픽 채워짐
  - 1개월: 매주 신규 brief 1~3건 정상 사이클
- **롤백 기준**: 2주 후에도 큐 변동 없으면 스캐너 로직 재점검 (NAVER API 응답 형식 변화 의심)
- **연관 PR**: 없음 (운영 액션)
- **Outcome (1주 후 작성)**: (대기 — 2026-05-27)
- **Outcome (1개월 후 작성)**: (대기 — 2026-06-20)

---

## D-2026-05-19-1: 본 로그 시작

- **층위**: 초기 셋업
- **변경**: [OODA.md](../../OODA.md) + [observations.template.md](observations.template.md) + 본 로그 신설.
- **근거 (Orient)**: docs/references/04-통합-3레이어-OS.md의 외부·실행·제어 3레이어
  각각에 명시적 의사결정 루프 부재. 향후 결정이 메모리에만 남아 6개월 후 미스터리 위험.
- **기대 효과**:
  - 1주: 첫 observations 스냅샷 작성 (Phase 1 운영 진입 시)
  - 1개월: 결정 ≥ 4개 누적 → 가중치·룰 추세 비교 가능
- **롤백 기준**: 4주 동안 결정 0건이면 OODA 캐던스 자체 재설계
- **연관 PR**: (초기 하네스 일괄)
- **Outcome (1주 후 작성)**: ✅ **달성 (2026-05-20)** — [observations/2026-W21.md](observations/2026-W21.md)
  첫 스냅샷 작성 완료. 본 결정에서 후속 결정 2건(D-2026-05-20-1, D-2026-05-20-2) 파생되어
  ADR lite 포맷이 의도대로 작동함을 검증. 1주 만에 누적 결정 3건 → 4주 기준 ×3 페이스.
- **Outcome (1개월 후 작성)**: (대기 — 2026-06-19)
