---
name: publish-daily
description: 오늘 발행 N편(기본 3) 자동 체인 — approved brief 선정부터 커밋·푸시까지
---

# publish-daily — 일일 발행 자동 체인

운영자가 `/publish-daily` (또는 `/publish-daily 5`)를 호출하면 오늘치 N편(기본 3)을
brief 선정부터 커밋·푸시까지 한 번에 처리한다. 이 절차는 실제 발행 세션에서
검증된 체인을 그대로 인코딩한 것이다 — 단계를 빼거나 순서를 바꾸지 마라.

## 입력

- `args`: 발행 편수 N (생략 시 3)
- `automation/briefs/{cluster}/*.brief.yaml` (status: approved 우선)
- `automation/ooda/calendar-2026-06.md` (있으면 오늘 날짜 행의 주제를 우선)

## 절차

### 1. approved brief 수집

`automation/briefs/{cluster}/*.brief.yaml`에서 `status: approved`인 brief를 N개
모은다. 부족하면:

- 발행 캘린더(`automation/ooda/calendar-2026-06.md`)의 오늘 행 또는 미커버
  고볼륨 주제로 brief를 신규 작성한다 (@brief-generator 규칙 준수 —
  `차별화:` 라인 필수, `_published_slugs.txt` 중복 차단).
- **운영자 즉석 승인 모드**: 원칙(CLAUDE.md 절대 원칙 3)상 `status: approved`는
  사람이 직접 편집한다. 본 스킬 실행 중 신규 brief가 필요하면 brief 요약
  (target_query·차별화·required_sources)을 운영자에게 보여주고 **승인 응답을
  받은 뒤에만** status를 approved로 바꾼다. 운영자가 세션에서 이미 "오늘 N편
  발행해"라고 명시 지시한 경우 그 지시를 즉석 승인으로 간주하되, 어떤 brief를
  즉석 승인 처리했는지 최종 보고에 명시한다.

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

```
git add (이번 발행 산출물만: src/content/answers/*.md, public/llms.txt,
         automation/briefs/**, 신규 diagrams 등)
git commit -m "feat: 3개 카테고리 동시 발행 (YYYY-MM-DD N편)"
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
