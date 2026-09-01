# Google 노출 회복 계획 — mureobom.com (2026-09-02)

> 운영 문서. 왜 하루 1편으로 줄였는지, 무엇을 바꿨는지, 운영자가 GSC에서 직접 해야 할 일과
> 회복을 어떻게 판정할지를 한 곳에 둔다. 미래 세션은 이 문서를 먼저 읽고 "3편으로 되돌리자"
> 같은 회귀를 제안하지 않는다.

## 1. 진단 — 무엇이 잘못됐나

| 지표 (GSC 28일) | 2026-06-28~07-25 | 2026-08-02~08-29 |
|---|---|---|
| 노출 | 174 | **99** |
| 클릭 | 0 | **0** |
| 평균 게재순위 | 12.6 | 12.2 |

같은 기간 발행 글은 218편 → 290편으로 늘었다. **글을 더 낼수록 노출이 줄었다.** 5/23~5/28에
하루 ~250회 노출 스파이크 후 6월부터 붕괴한 곡선은 Google 핵심 순위 시스템이 사이트 단위로
품질을 낮게 판정했을 때의 전형이다. 네이버는 같은 기간 실질 트래픽을 냈다(월 3천 노출대).

원인은 기술이 아니라 **콘텐츠 패턴**이다.

- 하루 3편 × 동일 템플릿(리드·표·인포그래픽·"흔한 오해"·FAQ 4~7개). 코퍼스 분석(2026-09-02):
  H2 "흔한 오해" 계열 189회, "정리 — 한 줄로" 72회, 화살표(→) 2회 이상 글 90편.
- Google 스팸 정책 "확장된 콘텐츠 악용"(생성 방법과 무관하게 **대량·저차별화** 페이지)과
  2026년 3월 코어·5월 코어·6월 스팸 업데이트가 정확히 이 패턴을 강등했다. 2026-07-16 Google
  Search Relations는 "크롤링됨 - 색인 생성되지 않음" 대량 발생이 사이트 단위 품질 의심 신호이며
  "AI로 쓴 티가 나고 고유한 것이 없는" 사이트를 예로 들었다.
- Google 공식 입장: AI 사용 자체는 문제가 아니다. 평가 대상은 **정확성·독창성·정보 이득·
  E-E-A-T**이며, 편집 없이 대량 생산된 콘텐츠가 강등된다.

## 2. 적용한 조치 (2026-09-02, 커밋 기준)

### 2-1. 캐던스 — 하루 3편 → **하루 1편**
- 클라우드 루틴 `06 mureobom (07:00)` (cron `0 22 * * *` UTC = 07:00 KST) 신설. 구 06:00 루틴은
  삭제됨. `/publish-daily` 기본 N=1, 오늘 발행분이 있으면 즉시 종료(§0 중복 차단).
- 추가 발행은 운영자가 세션에서 명시 지시할 때만(`/publish-daily 2`).
- 통과 후보가 없으면 **0편으로 끝내는 것이 정상**. 대체 글 급조 금지.

### 2-2. 본문 품질 기준 — Google 검색 프리미엄 콘텐츠 마스터 프롬프트 v4
- `docs/prompts/google-content-master-prompt-v4.md`를 레포에 두고 writer·quality-gate·geo가
  따른다. 핵심: 검색의도 → 사실 정확성 → 1차 출처 → **Information Gain(최소 2개)** →
  FACT/해석/추정/사례 구분 → 정보 기준일 → 중복·패딩 금지(체크리스트 1개, 화살표 1회) →
  결론=행동 계획 → FAQ=후속 질문만 → 구조는 검색의도별로 다르게.
- `docs/QUALITY_RUBRIC.md` 개정: 정보 이득·중복·문체 항목 추가, FAQPage 스키마 요건 삭제
  (Google이 2026-05 FAQ 리치 결과 폐지).
- compliance 룰 추가: W-03(화살표 2회 이상 차단), W-04(중복 블록 경고), V-05(대표 이미지 필수).

### 2-3. 검색 썸네일 — 글마다 WebP 대표 이미지 1장
- `scripts/gen_post_hero.mjs`: 본문 첫 인포그래픽 SVG를 1200×900(4:3) WebP로 래스터화해
  `public/img/{slug}.webp` 생성, 프론트매터 `hero` 삽입. 인포그래픽이 없는 초기 148편은
  제목·핵심 불릿 카드로 폴백. 290편 전체 백필 완료.
- 노출 경로: `og:image`(1순위, `og:image:type image/webp` + 폭·높이) → Article `image[]`·
  `thumbnailUrl` → WebPage `primaryImageOfPage` → 이미지 사이트맵 `<image:image>` → RSS/Atom
  `enclosure`, JSON Feed `image`. OG PNG(1200×630)는 2순위 `og:image`로 남겨 WebP를 못 읽는
  메신저 스크래퍼(카카오톡 등)에 대비.
- 근거: Google Article 구조화 데이터(가로 1200px 이상, 16:9·4:3·1:1), google-images.md
  "선호 이미지 지정"(primaryImageOfPage·og:image, 로고·텍스트 카드 지양), 네이버 콘텐츠 마크업
  (og:image 150×150 초과·5,000B 이상·3:1 이내·문서별 고유). `max-image-preview:large`는 기존 유지.
- 폰트는 레포 동봉 OFL(Gowun Batang·IBM Plex Sans KR, `scripts/fonts/`)만 사용 → 로컬·
  클라우드 출력 동일. `scripts/gen_post_og.py`도 같은 폰트로 전환하고 `--slug` 단건 모드 추가.

### 2-4. 기술 SEO 보완
- 내부 링크: `internalLinks`가 3개 미만이면 같은 클러스터 최신 글로 자동 보강("함께 보면
  좋은 글") — 고아 페이지 제거, "발견됨/크롤링됨 - 색인 생성되지 않음" 대응.
- JSON-LD: `WebPage`(primaryImageOfPage·isPartOf WebSite) 노드 추가, Article에 `articleSection`·
  `keywords`·`wordCount`·`thumbnailUrl`, `mainEntityOfPage`→WebPage `@id` 참조.
- OG: `article:section`·`article:tag`, `og:image:type/width/height` 정확화.
- `<title>` 구분자 `—` → `|` (Google title-link 권장 구분자, 발행 텍스트 긴 줄표 금지 정책 일관).
- 캐시: `/img/*` 하루 + SWR 1주.
- 사이트맵·RSS·robots·canonical·hreflang 불필요(단일 언어)·404·보안 헤더는 점검 결과 이상 없음.
  사이트맵은 `lastmod` 정직 유지(빌드 날짜 인플레이션 없음), 네이버 RSS는 본문 전문 CDATA·
  50건·10MB 미만 요건 충족.

### 2-5. 하지 않은 것 (의도적)
- **기발행 290편 제목·본문 소급 수정 없음** — 재색인 손실과 대량 변경 신호를 피한다. 대표
  이미지·내부링크·메타 보강만 페이지 템플릿 차원에서 일괄 적용.
- FAQPage JSON-LD 제거하지 않음 — 화면 FAQ와 일치하는 유효 스키마이며 Google이 "마크업 자체는
  문제 없음"이라 명시. 대신 신규 글부터 복사형 FAQ를 금지.
- 자동 색인 요청·프루닝(noindex/삭제) 자동화 없음 — 운영자 판단 영역.

## 3. 운영자가 직접 할 일 (GSC·서치어드바이저, 자동화 불가)

1. **GSC → 색인 생성 → 페이지**: "크롤링됨 - 현재 색인이 생성되지 않음" / "발견됨 - 현재 색인이
   생성되지 않음" 건수와 추세 확인. 이 비율이 회복의 1차 지표다.
2. **GSC → 보안 및 수동 조치**: 수동 조치(특히 "스팸성 콘텐츠"·"확장된 콘텐츠 악용")가 있으면
   재검토 요청이 필요하다. 조치 내용에 이 문서 §2를 요약해 첨부.
3. **GSC → Sitemaps**: `https://mureobom.com/sitemap.xml` 재제출(대표 이미지가 추가됐다).
4. **GSC → URL 검사**: 신규 발행 글(하루 1편)만 "색인 생성 요청". 290편 일괄 요청 금지.
5. **네이버 서치어드바이저**: 요청 → RSS(`/rss.xml`)·사이트맵 재제출, 사이트 진단에서 og:image·
   이미지 항목 재검사. 웹마스터 도구 → 수집 요청은 신규 글만.
6. **4주 뒤 판정** (§4).

## 4. 회복 판정 기준과 롤백

| 시점 | 기대 | 판정 |
|---|---|---|
| 2주 | GSC "크롤링됨 - 색인 안 됨" 증가 멈춤, 신규 글이 7일 내 색인 | 색인 안 되면 §3-1 재점검 |
| 4주 | 28일 노출 ≥ 300 (현 99의 3배), 클릭 > 0 | 미달이면 발행 주기 2일 1편으로 추가 감속 검토 |
| 8주 | 노출 ≥ 1,000, 상위 페이지 순위 < 10 다수 | 회복 확인 시에도 3편 복귀 금지(2편까지만 검토) |

롤백 기준: 대표 이미지 도입 후 4주 내 네이버 노출이 30% 이상 하락하면 og:image 1순위를 PNG로
되돌린다(`[slug].astro`의 `ogImage` 한 줄). 그 외 조치는 되돌릴 이유가 없다.

## 5. 참고 (수집한 근거)

- Google 검색 센터 — 스팸 정책 §확장된 콘텐츠 악용, 생성형 AI 콘텐츠 안내, 유용한 콘텐츠 제작
  ('누가·어떻게·왜'), Article 구조화 데이터, Google 이미지 모범 사례(선호 이미지 지정),
  robots meta `max-image-preview`, title-link (레포 사본: `docs/references/G-구글-공식가이드/`)
- 네이버 서치어드바이저 — 콘텐츠 마크업(오픈 그래프 이미지 요건), RSS·사이트맵 제출
  (레포 사본: `docs/references/H-네이버-공식가이드/`)
- 2026년 업데이트 정리: [Google June 2026 Spam Update](https://cliquestudios.com/university/resources/google-june-2026-spam-update),
  [March 2026 Core Update 콘텐츠 가이드](https://www.evertune.ai/resources/insights-on-ai/googles-march-2026-core-update-a-content-best-practices-guide-for-seo-and-ai-search),
  [Scaled Content Abuse 2026 정책](https://bulkbase.ai/seo/scaled-content-abuse-googles-policy-enforcement-how-to-stay-compliant-in-2026),
  [Crawled - Not Indexed: AI 콘텐츠 품질 신호(2026-07 Mueller·Splitt)](https://www.digitalapplied.com/blog/google-crawled-not-indexed-ai-content-quality-signal-2026),
  [FAQ 리치 결과 폐지(2026-05)](https://www.searchenginejournal.com/google-drops-faq-rich-results-from-search/574429/),
  [Article 이미지 비율 요건](https://www.searchenginejournal.com/google-updates-article-structured-data-guidelines/462334/),
  [카카오톡 og:image WebP 이슈](https://devtalk.kakao.com/t/webp/116191)
- 사이트 실측: `automation/ooda/gsc-summary-latest.md`, 코퍼스 패턴 분석(2026-09-02 세션)
