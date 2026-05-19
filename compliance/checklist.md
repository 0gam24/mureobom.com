# 컴플라이언스 체크리스트 — 물어봄

`compliance` 에이전트가 발행 직전에 모든 항목을 점검한다.
각 룰에는 ID가 있고, 차단 사유는 PR 코멘트에 ID로 기록한다.

## 0. 원본성 (모든 글)

| ID | 규칙 | 위반 시 |
|---|---|---|
| O-01 | 본문 인용 출처 ≥ 1건 | 차단 |
| O-02 | 모든 인용 URL이 research bundle에 존재 | 차단 |
| O-03 | bundle 외 도메인 URL 본문 노출 | 차단 |
| O-04 | 자체 코퍼스와 8-gram 자카드 유사도 ≤ 0.35 | 차단 |

## 1. 지식iN 데이터 격리

| ID | 규칙 | 위반 시 |
|---|---|---|
| K-01 | 본문/메타/FAQ에 `kin.naver.com` URL 없음 | 차단 |
| K-02 | "지식iN", "네이버 지식인" 텍스트 인용 없음 | 차단 |
| K-03 | 특정 사용자명/닉네임 인용 없음 | 차단 |
| K-04 | research 캐시에 kin 원문 흔적 없음 | 차단 + 캐시 삭제 |

## 2. 금융 표현 (loan, insurance 클러스터)

수익화는 AdSense 단독이므로 제휴·광고 표시 룰(구 F-02·F-03)은 제거.
정보 자체의 정확성·자문 회피만 강제.

| ID | 규칙 | 위반 시 |
|---|---|---|
| F-01 | 단정적 금리/한도/수익률 약속("최저 X%", "무조건 승인") | 차단 |
| F-02 | 특정 금융 상품·기관 추천("OO은행이 가장 유리") | 차단 |
| F-03 | 보험 상품 비교는 동일 보장범위 기준 명시 | 경고 |

## 3. 법률·의료·세무 (tax, support 클러스터)

| ID | 규칙 | 위반 시 |
|---|---|---|
| L-01 | "반드시 ~해야 합니다", "~을 보장합니다" 단정 표현 | 경고 |
| L-02 | 연도 기준 명시(`{N}년 기준`) — must_cover에 연도 의존 항목 있을 때 | 차단 |
| L-03 | 일반 정보 고지(`이 글은 일반 정보이며 ...`) 필수 — disclaimer 플래그 true일 때 | 차단 |

## 4. 본문 무결성 (제휴 폐기 후 잔존 룰)

| ID | 규칙 | 위반 시 |
|---|---|---|
| A-01 | 본문에 가격·할인 약속 — 출처 없으면 | 차단 |
| A-02 | 본문에 외부 링크(공식 출처 외) — 차단 (제휴·계산기 CTA 폐기 정책) | 차단 |

## 5. 메타 / 구조 / SEO

| ID | 규칙 | 위반 시 |
|---|---|---|
| M-01 | `summary` 30~160자 (SERP description 절단 회피) | 차단(Zod) |
| M-02 | `title` 10~60자 (Google `<title>` 권장) | 차단(Zod) |
| M-03 | `faq` 길이 ≥ brief.geo.faq_pairs_min | 차단 |
| M-04 | `internalLinks`가 발행된 슬러그만 가리킴 | 자동 수정 |
| M-05 | `<!-- BLOCKED -->` 마커 잔존 | 차단 |
| M-06 | 프론트매터가 [src/content/config.ts](../src/content/config.ts) Zod 스키마 통과 | 차단(빌드 단계) |
| M-07 | 각 페이지에 canonical URL 노출 (Base.astro가 자동) — 사라지면 차단 | 차단 |
| M-08 | 각 글에 Article + BreadcrumbList JSON-LD 노출 (`[slug].astro` @graph) — Rich Results Test 통과 | 경고 |
| M-09 | `public/robots.txt` 존재 + `public/sitemap.xml` 라우트 (`/sitemap.xml`) 응답 200 | 차단 |

## 6. 디자인 시스템 (프론트엔드 PR 전용)

| ID | 규칙 | 위반 시 |
|---|---|---|
| D-01 | `src/components/**`·`src/layouts/**`·`src/pages/**`에 하드코딩 색(`#xxx`, `rgb(...)`, 명명색) 없음. `var(--…)` 토큰만 | 경고 |
| D-02 | 하드코딩 간격(`Npx`, `Nrem` 직접 값) 대신 `--gap`/`--maxw`/`--measure` 토큰 사용 | 경고 |
| D-03 | 새 색·간격은 [src/styles/tokens.css](../src/styles/tokens.css)에 변수 추가 후 사용 | 경고 |

D-* 룰은 본문(answers) PR엔 적용 X — 마크다운에는 인라인 스타일이 없음.

## 7. AdSense 정책 가드 (수익화 단독 채널)

| ID | 규칙 | 위반 시 |
|---|---|---|
| AD-01 | `public/ads.txt` 존재 + 한 줄 이상의 유효 publisher 라인 (`google.com, pub-…, DIRECT, …`) | 차단(빌드 단계 권장) |
| AD-02 | 본문 길이 ≥ 700자 (공백 제외) — 빈약 콘텐츠 광고 정책 회피 | 차단 |
| AD-03 | AdSense 금지 카테고리 텍스트 미포함 (도박·성인·폭력·약물·무기 관련 명백한 단어) | 차단 |
| AD-04 | 광고 슬롯 `<AdSlot>`은 페이지당 최대 2개. 위치 = `top`(요약-본문 사이) + `bottom`(FAQ-고지 사이). **출처 박스 위·아래 배치 금지**. FAQ 없으면 bottom 슬롯 미노출 | 차단 |
| AD-05 | 의료·법률·금융 자문 단정 표현 없음 + `disclaimer: true` 유지 (AdSense YMYL 정책) | 차단 |
| AD-06 | `<AdSlot>` 컴포넌트 외 광고 코드 삽입 금지 (Auto Ads/`<script>` 직접 삽입 차단) | 차단 |
| AD-07 | publisher ID·slot ID는 `.env`에서만 — 본문/컴포넌트 하드코딩 금지 | 차단 |

AdSense 승인 전(MVP 단계) AD-01·AD-07은 경고로 격하 가능, 승인 후 차단으로 격상.

## 차단 보고 포맷

```
compliance BLOCK: {slug} — {RULE_ID}: {1줄 사유}
```

여러 룰 위반 시 모두 나열. PR 코멘트 + brief.human_notes에 누적.
