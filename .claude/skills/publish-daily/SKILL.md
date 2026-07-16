---
name: publish-daily
description: 오늘 발행 N편(기본 3) 자동 체인 — approved brief 선정부터 커밋·푸시까지
---

# publish-daily — 일일 발행 자동 체인

운영자가 `/publish-daily` (또는 `/publish-daily 5`)를 호출하면 오늘치 N편(기본 3)을
brief 선정부터 커밋·푸시까지 한 번에 처리한다. 이 절차는 실제 발행 세션에서
검증된 체인을 그대로 인코딩한 것이다 — 단계를 빼거나 순서를 바꾸지 마라.

## 날짜·시간 기준 — 항상 KST(Asia/Seoul)

이 사이트의 **모든 날짜·시간은 한국시간(KST) 기준**이다. 예외 없음.

- 오늘 날짜는 반드시 `TZ=Asia/Seoul date +%F`로 구해 변수로 두고 사용한다.
  프론트매터 `published`·`updated`, 커밋 메시지 날짜, 보고서 날짜 모두 이 값.
- **클라우드(스케줄) 실행은 UTC 시계**다. 그냥 `date`(UTC)를 쓰면 새벽 발행이
  하루 빨리 찍힌다(04:30 KST = 전날 19:30 UTC). 절대 `date`(UTC)를 날짜 소스로
  쓰지 마라. 로컬(운영자 PC)은 KST라 문제없지만, 습관적으로 `TZ=Asia/Seoul`을 붙인다.
- 자동 배포 스케줄은 매일 **04:30 KST**(cron `30 19 * * *` UTC) 발화. 한국은 서머타임이
  없어 이 매핑은 연중 고정. 파이프라인은 발화 후 약 30~60분 걸리므로 완료는 05:00~05:30 KST.

## 입력

- `args`: 발행 편수 N (생략 시 3)
- `automation/topic-queue.json` — **1차 토픽 소스** (스캐너 산출). `score` 내림차순,
  `is_covered`를 통과한 신규 키워드. 시드 + kin 제목 마이닝 파생 롱테일 포함.
- `automation/briefs/{cluster}/*.brief.yaml` — `status: approved` 잔여분 있으면 먼저 소진.
- `automation/ooda/calendar-2026-06.md` — **폴백**. 큐가 비었거나 stale(직전 발행
  이후 미갱신)일 때만 사용. 큐가 채워지면 캘린더는 비활성.

## 토픽 소스 우선순위 (D-2026-06-15 — 스캐너 큐 주도로 전환)

```
1. approved brief 잔여분         (사람이 이미 승인 → 즉시 사용)
2. topic-queue.json 상위 신규    (스캐너 발견 키워드 → brief 초안 → 즉석 승인)
3. calendar-2026-06.md 오늘 행   (큐가 비었을 때만 폴백)
```

> **왜 큐 주도인가**: 캘린더는 사람이 수동 큐레이션한 한시적 목록(6/25 소진).
> 스캐너가 `is_covered`(의미중복 차단) + 파생 질의 마이닝을 갖추면서 **요즘 실제로
> 많이 묻는 신규 롱테일**을 자동 발견한다 → 이게 지속 가능한 토픽 엔진. 캘린더는
> 큐가 마르거나 시즌 선점이 필요할 때의 보조 수단으로만 남긴다.

## 절차

### 1. 토픽 선정 + brief 확보

위 우선순위대로 N개 토픽을 모은다.

- **큐에서 선정**: `automation/topic-queue.json`을 score 내림차순으로 읽고,
  `_published_slugs.txt`와 다시 한 번 대조(스캐너가 1차 차단하지만 큐 생성 이후
  발행분 반영). 클러스터 배분(2단계)에 맞춰 상위 항목을 고른다.
- **brief 초안**: 선정된 큐 항목마다 brief가 없으면 `@brief-generator`로 초안 작성
  (`차별화:` 라인 필수). 파생 키워드는 `target_query`를 사람이 검색창에 칠 자연어로
  다듬는다.
- **운영자 즉석 승인 모드**: 원칙(CLAUDE.md 절대 원칙 3)상 `status: approved`는
  사람이 직접 편집한다. 신규 brief가 필요하면 요약(target_query·차별화·
  required_sources)을 운영자에게 보여주고 **승인 응답을 받은 뒤에만** approved로
  바꾼다. 운영자가 세션에서 이미 "오늘 N편 발행해"(또는 "루프 실행")라고 명시
  지시한 경우 그 지시를 즉석 승인으로 간주하되, **어떤 brief를 즉석 승인 처리했는지
  최종 보고에 명시한다**.
- **지식iN 가드**: 큐 키워드는 신호로 발견했을 뿐, 본문은 항상 공식 1차 출처로
  원본 작성(절대 원칙 1·2). 파생 질의도 짧은 키워드 구일 뿐 질문 원문이 아니다.

### 2. 클러스터 배분 — loan·tax 우선

N편의 클러스터를 배분한다. 기본 N=3이면 `loan 1 + tax 1 + (support/insurance
교대 1)` — RPM 높은 loan·tax를 매일 고정하고 support/insurance는 격일 교대
(decisions.log.md D-2026-06-11-3). N>3이면 loan·tax에 먼저 추가 배분.

### 3. 에이전트 직렬 체인 × N편 병렬

각 편마다 아래 직렬 체인을 돌린다. 편끼리는 병렬 가능 (파일 충돌 없음 —
글 단위로 산출 파일이 분리됨).

```
@researcher  → automation/research/{cluster}/{slug}.research.yaml
@writer      → src/content/answers/{slug}.md
@quality-gate → 85점 게이트. REVISE면 writer 1회 수정 후 재채점,
                재채점 85 미만 또는 KILL이면 해당 편 폐기(보고에 사유 기록)
@geo         → faq 보강 + llms.txt
@compliance  → 통과 시 brief status: published + _published_slugs.txt 추가
```

effort는 WORKFLOW.md §3 표 그대로 (researcher·writer·quality-gate·compliance
xhigh, geo medium).

### 4. llms.txt 재생성

```
python scripts/gen_llms_posts.py
```

POSTS:auto 마커 사이를 전체 재생성 — geo의 수동 한 줄 추가와 어긋나도
이 스크립트 출력이 최종이다.

### 5. 빌드 검증

```
npm run build
```

Zod 스키마(sources min 1, title/summary 길이) 위반이 있으면 여기서 실패한다.
실패 시 해당 글을 고치고 재빌드 — 빌드 실패 상태로 6단계에 가지 마라.

### 6. 커밋·푸시

`YYYY-MM-DD`는 **KST 오늘 날짜**(`TZ=Asia/Seoul date +%F`). 프론트매터
`published`·`updated`와 커밋 메시지가 모두 같은 KST 날짜여야 한다.

```
git add (이번 발행 산출물만: src/content/answers/*.md, public/llms.txt,
         automation/briefs/**, 신규 diagrams 등)
git commit -m "feat: 3개 카테고리 동시 발행 (YYYY-MM-DD N편)"   # YYYY-MM-DD = KST
git push
```

### 7. 링크 보고

최종 한 줄 보고 + 발행 URL 목록:

```
published N편: 
- https://mureobom.com/{cluster}/{slug}/ — {title}
...
(폐기/REVISE 발생 시 사유 요약)
```

## 절대 금지

- quality-gate REVISE 2회 이상 허용 (1회 원칙 — QUALITY_RUBRIC.md)
- 빌드 실패 상태 커밋
- 지식iN 원문/URL 유입 (PreToolUse 훅이 차단하지만 시도 자체 금지)
- `_published_slugs.txt`에 있는 슬러그 재발행
