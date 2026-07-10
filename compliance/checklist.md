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
| AD-01 | `public/ads.txt` 존재 + 한 줄 이상의 유효 publisher 라인 (`google.com, pub-{16자리숫자}, DIRECT, f08c47fec0942fa0`). `pub-PUBLISHER_ID` placeholder 잔존 시 차단 | 차단 |
| AD-02 | 본문 길이 ≥ 700자 (공백 제외) — 빈약 콘텐츠 광고 정책 회피 | 차단 |
| AD-03 | AdSense 금지 카테고리 텍스트 미포함 (도박·성인·폭력·약물·무기 관련 명백한 단어) | 차단 |
| AD-04 | 광고 슬롯 `<AdSlot>`은 페이지당 최대 2개. 위치 = `top`(요약-본문 사이) + `bottom`(FAQ-고지 사이). **출처 박스 위·아래 배치 금지**. FAQ 없으면 bottom 슬롯 미노출 | 차단 |
| AD-05 | 의료·법률·금융 자문 단정 표현 없음 + `disclaimer: true` 유지 (AdSense YMYL 정책) | 차단 |
| AD-06 | `<AdSlot>` 컴포넌트 외 광고 코드 삽입 금지 (Auto Ads/`<script>` 직접 삽입 차단) | 차단 |
| AD-07 | publisher ID(`ca-pub-…`)·slot ID는 `.env.local` 또는 Cloudflare Pages env에서만. 본문 산출물(`src/content/answers/**`, `automation/briefs/**`, `public/llms.txt`)에 직접 노출 시 차단 | 차단 |

2026-05-20 AdSense 사이트 추가 후 publisher ID 실값(`ca-pub-7830821732287404`)이
[public/ads.txt](../public/ads.txt) + Cloudflare Pages env에 등록 완료 — AD-01·AD-07
**경고 → 차단 격상**.

## 8. 작성 주체 · E-E-A-T (E-*)

프론트매터 `author`(기본 `물어봄 편집부`)는 레이아웃이 바이라인 + JSON-LD Article
`author`로 자동 렌더한다. 바이라인은 "{author} 작성 · 공식 1차 출처 대조 검수 …
이 글은 어떻게 만드나요?(→/about/#how)" 형태.

| ID | 규칙 | 위반 시 |
|---|---|---|
| E-01 | 프론트매터 `author`는 정직한 편집 조직 라벨만 (`물어봄 편집부` 또는 `물어봄 {세금/대출/지원/보험}팀`). 3~20자 | 차단 |
| E-02 | **실재하지 않는 개인 전문가·자격 사칭 금지** — author나 본문/바이라인에 "세무사·변호사·노무사·회계사·감정평가사·전문가 검수" 등 자격 표현을 특정 개인/이름과 함께 쓰면 차단(실재 자격 보유자 협업 근거가 레포에 없으면 위반). 조직 차원의 '공식 1차 출처 대조 검수'는 허용 | 차단 |
| E-03 | 상세 페이지 바이라인·JSON-LD `author`는 레이아웃이 자동 렌더 — 본문에 중복 작성자 마크업 금지 | 차단 |

## 9. 인포그래픽 · 시각자료 (V-*)

모든 신규 글은 본문에 `public/diagrams/{slug}.svg` 인포그래픽 1개 이상을
`![alt](/diagrams/{slug}.svg)`로 포함한다. D-01 정신(브랜드 팔레트 강제)의 SVG 확장.

| ID | 규칙 | 위반 시 |
|---|---|---|
| V-01 | 신규 글은 본문에 `/diagrams/{slug}.svg` 인포그래픽을 1개 이상 포함 (파일 실재 + 본문 참조 둘 다). 없으면 차단. (기존 글 소급은 예외) | 차단 |
| V-02 | SVG는 브랜드 팔레트 hex(`#FBF7F0`·`#F4EEE2`·`#1A2B2A`·`#4A5856`·`#8A938F`·`#0E7C72`·`#0A5F58`·`#E3F0EE`·`#C2873B`·`#E3DCCF`·`#B5462F`)만 사용. 이 밖의 색상 하드코딩 시 차단 (D-01 정신의 SVG 확장) | 차단 |
| V-03 | SVG에 외부 폰트/외부 이미지/raster/`<script>` 금지, alt 텍스트에 도표 핵심 정보 포함 (a11y·SEO) | 경고 |
| V-04 | 인포그래픽은 정보 전달용(흐름·비교·타임라인·체크리스트). 순수 장식 금지 | 경고 |

## 10. 공유 기능 (Share)

| ID | 규칙 | 위반 시 |
|---|---|---|
| SH-01 | `<ShareButtons>` 컴포넌트는 페이지당 최대 1회. 배치는 `disclaimer` 직후·`</article>` 직전. **출처 박스(`aside.sources`)·FAQ·`<AdSlot>` 직접 인접 금지** (AD-04 정신 확장) | 차단 |
| SH-02 | 외부 공유 SDK(`kakao.min.js`, `sdk.facebook.net` 등) 로드 금지. Web Share API + `navigator.clipboard` + 카카오 share URL(`sharer.kakao.com/...`)만 허용 — SDK 도입은 광고 차단기·CSP·LCP 영향 | 차단 |
| SH-03 | 복사·공유 대상 URL은 반드시 `<link rel="canonical">` 값과 동일. `location.href` 직접 사용 금지 — `?utm_*`·앵커 묻으면 중복 색인 위험 (GEO 가드) | 차단 |
| SH-04 | 공유 클릭 추적용 외부 스크립트(GA·Plausible·픽셀) 도입 금지. 외부 추적 도입은 본 룰을 갱신해 분리 PR로 | 경고 |

## 11. 문체 — AI 생성 티 제거 (W-*)

> 배경: 긴 줄표(—·–)와 매 글 반복되는 상투구는 대표적인 AI 문체 신호다.
> AdSense 심사·검색 품질평가에서 "AI로 찍어낸 사이트" 인상을 주므로 신규 발행분부터 금지.
> **기발행 글 소급 수정 금지** — 제목 변경은 재색인 유발로 검색 순위에 손해(V-01 소급 예외와 동일 원칙).

| ID | 규칙 | 위반 시 |
|---|---|---|
| W-01 | **신규 글**의 발행 노출 텍스트(`title`·`summary`·본문·`faq`·인포그래픽 SVG 내 텍스트)에 긴 줄표(em dash `—` U+2014, en dash `–` U+2013) 사용 금지. 쉼표·가운뎃점(`·`)·괄호·문장 분리로 대체. 예: ❌ `교육비 세액공제 2026 — 자녀 300만` → ✅ `교육비 세액공제 2026, 자녀 300만 대학 900만`. (automation/·docs/·소스코드 주석 등 내부 파일은 적용 제외) | 차단 |
| W-02 | 상투구 반복 금지 — `핵심은 N가지`, `정리하면`, `결론부터 말하면`, `한눈에 정리` 류 표현을 모든 글에서 동일하게 반복하지 말 것. 같은 글 구조(리드·표·FAQ)라도 문장 패턴은 글마다 다양화 | 경고 |

## 차단 보고 포맷

```
compliance BLOCK: {slug} — {RULE_ID}: {1줄 사유}
```

여러 룰 위반 시 모두 나열. PR 코멘트 + brief.human_notes에 누적.
