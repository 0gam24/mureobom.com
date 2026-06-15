# CLAUDE.md — 물어봄(mureobom.com)

이 파일은 미래의 Claude 세션이 본 레포에서 일할 때 절대 어겨선 안 되는 규칙과
파이프라인 구조를 한 번에 흡수하기 위한 운영 가이드다.

## 절대 원칙 (위반 시 작업 중단)

1. **네이버 데이터는 신호로만**. 지식iN 질문/답변 원문·캡처·장문 인용을 저장하거나
   재게시하지 않는다. `signal` 필드에는 집계 수치만 들어간다.
   → 강제 장치: [.claude/settings.json](.claude/settings.json) deny + 
   [scripts/hooks/no_kin_originals.py](scripts/hooks/no_kin_originals.py) PreToolUse 훅이
   `automation/briefs/{cluster}/*.brief.yaml`, `src/content/answers/**`,
   `public/llms.txt`에 `kin.naver.com`/`지식iN` 유입을 자동 차단한다.
2. **공식 1차 출처 기반 원본만 발행**. 법령·정부·KFTC·FSS·공단 자료를 인용한다.
   `sources`가 0건이면 Astro 콘텐츠 컬렉션 Zod 스키마(`src/content/config.ts`)와
   compliance 에이전트가 동시에 빌드/발행을 차단한다.
   → WebFetch는 settings.json 화이트리스트 도메인(law.go.kr·moel.go.kr·
   nts.go.kr·fss.or.kr·kftc.or.kr 등)으로만 허용.
3. **사람 개입은 brief 검수만**. brief.yaml의 `status: approved` 이후 단계는 무인.
4. **컴플라이언스 게이트 우회 금지**. AdSense 정책(원본 콘텐츠·금지 카테고리·
   일반정보 고지)·금융표현(단정적 약속 금지)·자체 코퍼스+웹 유사도 검사를
   통과하지 못한 글은 머지하지 않는다.

운영자 슬래시 명령어 사용 순서는 [WORKFLOW.md](WORKFLOW.md) 참조.
의사결정 루프(주간 OODA·브리프 검수·에이전트 핸드오프)는 [OODA.md](OODA.md) 참조.

## 사이트 IA

```
mureobom.com
├─ /tax        세금 (연말정산·종합소득세·부가세·양도세)
├─ /support    정부지원금 (실업급여·근로장려금·바우처·청년지원)
├─ /loan       대출·신용 (전세·주담대·신용대출·신용점수)
└─ /insurance  보험·연금 (4대보험·국민연금·실손·연금저축)
```

포스트 URL: `/{cluster}/{slug}`. 4 카테고리 외 신규 클러스터는 기획 변경 PR 필요.

## 디렉토리 구조 (Astro 루트 + automation 형제 분리)

```
mureobom/                       ← 레포 루트 = Astro 프로젝트 루트
├─ astro.config.mjs             (npm create astro 후 생성, 아직 없음)
├─ package.json                 (동상)
├─ src/
│  ├─ styles/tokens.css
│  ├─ layouts/Base.astro
│  ├─ components/
│  │  ├─ QuestionCard.astro
│  │  └─ AdSlot.astro            AdSense 광고 슬롯 (in-article x2)
│  ├─ content/
│  │  ├─ config.ts              Zod 스키마(answers 컬렉션)
│  │  └─ answers/               ← 작성 에이전트가 *.md 생성하는 곳
│  └─ pages/
│     ├─ index.astro
│     ├─ sitemap.xml.ts        동적 sitemap (홈+카테고리+모든 글)
│     └─ [cluster]/
│        ├─ index.astro
│        └─ [slug].astro        Article+BreadcrumbList+FAQPage @graph
├─ automation/                  ← 백엔드 파이프라인 (Astro 빌드 제외)
│  ├─ config/
│  │  ├─ seed-keywords.yaml     클러스터별 시드 + aliases
│  │  └─ scoring.yaml           점수 가중치 + 스캐너 파라미터
│  ├─ scripts/topic_scanner.py  cron이 호출
│  ├─ briefs/
│  │  ├─ _schema.md             brief.yaml 스키마
│  │  ├─ _published_slugs.txt   발행 완료 슬러그
│  │  ├─ example.brief.yaml     참조용
│  │  └─ {cluster}/{slug}.brief.yaml
│  ├─ research/{cluster}/       researcher 산출 (.research.yaml, gitignore)
│  ├─ ooda/                     Macro OODA 산출
│  │  ├─ observations.template.md  주간 메트릭 스냅샷 양식
│  │  ├─ observations/{YYYY-WW}.md 실제 주차별 (.gitkeep로 폴더만)
│  │  ├─ calendar-2026-06.md    14일 발행 캘린더 (6/12~6/25)
│  │  └─ decisions.log.md       결정 로그 (역시간순 ADR)
│  └─ topic-queue.json          스캐너 산출 (처음엔 없음)
├─ .github/workflows/
│  ├─ topic-scanner.yml
│  └─ indexnow.yml              새 글 push 시 Bing·Naver 색인 ping
├─ .claude/
│  ├─ settings.json             permissions + PreToolUse 훅
│  ├─ agents/                   6개 파이프라인 에이전트
│  └─ skills/publish-daily/     일 3편 발행 원커맨드 체인
├─ scripts/
│  ├─ gen_llms_posts.py         llms.txt POSTS 블록 재생성 (geo가 호출)
│  ├─ backfill_published.py     published: 백필 (updated 캡)
│  └─ hooks/
│     ├─ no_kin_originals.py    본문 산출물의 kin 유입 차단
│     └─ _test.py               훅 단위 테스트
├─ compliance/checklist.md      KFTC + FSS 체크리스트
├─ templates/post.md            본문 구조 템플릿
├─ public/
│  ├─ llms.txt                  GEO 에이전트가 갱신
│  ├─ ads.txt                   Google AdSense publisher 검증
│  ├─ robots.txt                크롤러 허용 + sitemap 위치
│  ├─ favicon.svg               브랜드 아이콘 (워터틸 + ?)
│  ├─ og-default.svg            디자인 소스 SVG (편집용)
│  ├─ og-default.png            1200×630 SNS 미리보기 (scripts/gen_og_default.py 생성)
│  └─ apple-touch-icon.png      180×180 iOS 홈스크린 (scripts/gen_apple_touch_icon.py)
│
│  ⓘ 디자인 자산 재생성:
│    python scripts/gen_og_default.py        # 브랜드 색·문구 변경 시
│    python scripts/gen_apple_touch_icon.py
│    토큰은 src/styles/tokens.css의 hex 값을 그대로 스크립트 상수로 가져옴.
├─ docs/
│  ├─ 기획서.md                 백엔드 마스터 기획
│  └─ frontend-기획서.md
├─ preview.html                 디자인 확인용 (빌드 제외)
├─ CLAUDE.md
├─ WORKFLOW.md                  운영자 슬래시 명령어 맵
└─ OODA.md                      Macro/Micro/Agent 의사결정 루프 정의
```

## 파이프라인 한 줄 요약

```
cron 스캐너 → automation/topic-queue.json → brief 초안 → 사람 15분 검수(approved)
  → researcher → writer(src/content/answers/{slug}.md 직접 작성)
  → quality-gate(85점 게이트, REVISE 1회) → GEO → compliance
  → auto-PR → CI 통과 시 auto-merge
```

각 단계 에이전트의 입출력 계약은 [.claude/agents/](.claude/agents/) 내 정의 참조.
프론트매터 스키마는 [src/content/config.ts](src/content/config.ts) Zod로 강제됨.

## 점수 로직

```
score = 100 * ( 0.40·trend_momentum
              + 0.30·question_volume
              + 0.20·(cluster_fit · cluster_fit_boost)   # loan 1.15 / tax 1.10
              + 0.10·freshness )
```

의미중복(기발행 포함) 후보는 점수 감점이 아니라 `is_covered()`로 **큐에서 하드 스킵**.
가중치 변경은 [automation/config/scoring.yaml](automation/config/scoring.yaml)에서만.
1주차 PoC 데이터로 튜닝.

## 자주 마주칠 함정

- **kin API에 게시일 필드가 빈약**.
  [automation/scripts/topic_scanner.py](automation/scripts/topic_scanner.py)의
  `_estimate_age_days`는 postdate → description 정규식 → 위치 프록시 순으로 폴백.
  1주차 실측에서 (1)/(2)가 잡히는 비율이 충분하면 위치 프록시 가중치를 낮춰라.
- **API 일일 한도 ~25,000회**. 시드당 데이터랩+kin 2회 + 파생 질의당 kin 1회.
  현재 4×10×(2 + 최대 3) ≈ 200회/일 (한도 대비 여유). `max_derived_per_seed` 상향·
  세분 시드 추가 시 재계산.
  → 한도 압박 시 **시드 묶음 / 결과 캐싱 / 동일 키워드 N일 재호출 금지** 도입
  (현재 미구현). 1주차 실측이 ~30% 이상이면 즉시 캐싱 추가.
- **중복 발행 방지는 2단**. (1) 스캐너 `is_covered()`가 `_published_slugs.txt`에 대해
  **같은 클러스터 내 부분문자열(의미중복)**을 하드 스킵 — 시드형 후보(`마이너스통장`)가
  구체 발행 슬러그(`마이너스통장-한도-금리`)에 포함되면 큐에서 제외. (2) compliance
  에이전트의 임베딩/유사도 최종 검사. (구 정확 슬러그 매칭 dup_penalty는 폐기.)
- **클러스터는 폴더 아닌 프론트매터 필드**. Astro `answers` 컬렉션은 평면이고
  라우팅은 [src/pages/[cluster]/[slug].astro](src/pages/[cluster]/[slug].astro)가
  `cluster` 필드로 필터한다.
- **파생 질의 구현됨 (D-2026-06-15)**. `topic_scanner.derive_queries()`가 시드 kin
  제목에서 ≥2회 등장한 명사 토큰을 뽑아 `{시드} {토큰}` 롱테일 후보를 만들고 자체
  kin_search로 실측 신호를 얻는다(트렌드 미측정, cluster_fit 하한 0.6). **제목 원문은
  보관하지 않고 토큰 빈도만 집계** — 절대 원칙 1 유지. 한도는 scoring.yaml
  `max_derived_per_seed`(현 3). 이게 "요즘 많이 묻는 신규 질문"을 자동 발굴하는
  핵심 — 큐가 시드 40개에 갇히지 않고 롱테일로 확장된다.

## 개발 시 주의

- 본문/리서치 캐시에 지식iN 원문을 절대 저장하지 않는다. 캐시 디렉토리도 만들지 마라.
- `automation/briefs/*.brief.yaml`의 `signal` 필드에는 점수와 0~1 정규화 값만.
  개별 질문 문장 금지.
- 새 카테고리·새 시드 추가는 기획 변경. PR 설명에 사유와 기대 효과 명시.
- `src/` 와 `automation/`은 형제 디렉토리. Astro 빌드는 `src/`만 처리한다.

## 디자인 시스템 규칙

브랜드 컨셉: **물(신뢰·차분) + 봄(친근·새싹)** — 따뜻한 종이 + 명조 + 워터틸.

- **단일 소스**: [src/styles/tokens.css](src/styles/tokens.css)가 색·간격·타이포의
  유일한 정의. 컴포넌트(`.astro`/`<style>`)는 `var(--paper)`, `var(--teal)`,
  `var(--gap)` 등 토큰만 참조. **하드코딩된 hex/rgb/px 값 금지**.
- 시그니처: `#0E7C72`(워터틸) + `#FBF7F0`(크림 종이). 명조 헤드라인
  (`Gowun Batang`) + `IBM Plex Sans KR` 본문. line-height 1.85 (한국어 가독성).
- 모티프: 로고의 `봄`을 틸로 + `.sprout` 새싹 글리프, 카드 배경에 옅은 "?" 텍스처.

### 의도적으로 회피하는 기본값 (Why)

미래 세션이 "익숙한 기본값"으로 드리프트하지 않도록 명시:

| 회피 대상 | 이유 |
|---|---|
| 순백색 배경 `#FFFFFF` | AI 슬롭 인상. `--paper #FBF7F0`(크림)으로 종이 신뢰감 |
| `Pretendard` 한국어 sans | 식상함 회피. 명조 헤드라인 + Plex Sans 본문 |
| 헤드라인 sans-serif | 정보·신뢰 톤 약화. 헤드라인은 무조건 `--font-display` (명조) |
| 순검정 텍스트 `#000000` | 차분함 손상. `--ink #1A2B2A` 워터잉크 |
| `line-height: 1.5` 본문 | 한국어 장문 가독성 부족. 본문은 `--lh-body: 1.85` |

### 레이아웃 불변 (변경 시 PR 사유 필수)

- **상세 페이지 본문 직후 "확인한 공식 자료" 박스 고정** —
  [src/pages/\[cluster\]/\[slug\].astro](src/pages/[cluster]/[slug].astro) 구조 그대로.
  E-E-A-T 신호 + 원본성을 시각적으로 보장하는 핵심 신뢰 장치.
- **`sources` 0건이면 빌드 차단** — [src/content/config.ts](src/content/config.ts)
  Zod `min(1)`이 1차, [compliance/checklist.md](compliance/checklist.md) O-01이 2차.
  이 가드를 우회하지 마라.
- 카테고리 랜딩 → 상세 페이지 카드 컴포넌트는
  [src/components/QuestionCard.astro](src/components/QuestionCard.astro) 공용 — 카드
  스타일 변경은 홈·랜딩에 동시 반영된다.

## 아키텍처 불변

- **새 글 = 마크다운 1개**. `src/content/answers/{slug}.md` 1개를 추가하면 빌드가
  홈 피드·카테고리 랜딩·상세 페이지·사이트맵·llms.txt까지 자동 반영. 별도 라우트
  등록·메뉴 편집 불필요. 이 약속을 깨는 변경(예: 글 단위 수동 등록 단계 추가)은
  무인 파이프라인 전제를 무너뜨린다.
- **brief 단계와 본문 단계 분리**. `automation/`(brief·signal·research)과
  `src/`(발행 본문)는 형제. 자동화 산출은 Astro 빌드에 들어가지 않고,
  발행 본문은 자동화 메타를 노출하지 않는다.

## brief.yaml ↔ Astro 프론트매터 매핑

작성 에이전트가 brief 승인 필드를 변환해 `src/content/answers/{slug}.md`
프론트매터로 옮긴다. **반드시 이 표대로** (Zod 스키마와 1:1):

| brief.yaml (snake_case) | frontmatter (camelCase) | 비고 |
|---|---|---|
| `id` | — | 파일명 `{slug}.md`로만 표현 |
| `cluster` | `cluster` | Zod enum 4종 |
| `status` | — | brief 측 상태, 프론트엔드 노출 X |
| `target_query` | `targetQuery` | 자연어 그대로 |
| `search_intent` | `searchIntent` | 정보형/절차형/거래형 |
| `signal` | — | 점수 메타, 프론트엔드 노출 X |
| `must_cover` | — | 본문 섹션 구성에만 사용 |
| `required_sources` | `sources` | `[{label, url}]`로 구조화, **min 1** |
| `internal_links` | `internalLinks` | 발행된 슬러그만 |
| (구 `cta`) | — | **삭제**. 수익화는 AdSense (페이지 슬롯) — brief 단위 CTA 필드 불필요 |
| `compliance` | — | 게이트 메타, 프론트엔드 노출 X |
| `geo.faq_pairs_min` | (→ `faq` 길이로 강제) | geo 에이전트가 충족 |
| `geo.faq_pairs` | `faq` | `[{q, a}]` — FAQPage JSON-LD 자동 생성 |
| `human_notes` | — | 검수 메모, 프론트엔드 노출 X |
| (writer 신규) | `title` | 질문형 제목, **Zod 10~60자** (Google `<title>` 권장) |
| (writer 신규) | `summary` | 한 문장 핵심 답, **Zod 30~160자** (SERP 절단 회피) |
| (writer 신규) | `updated` | 발행 일자 (ISO date) |
| (writer 신규) | `disclaimer` | 기본 true — 일반정보 고지 노출 |
| (writer 선택) | `image` | OG/Twitter 이미지 절대경로. 미지정 시 `/og-default.png` |

엔드포인트 스키마 정의: [src/content/config.ts](src/content/config.ts).

## 수익화 — Google AdSense 단독

mureobom은 **AdSense 광고 수익만** 운영한다. **계산기 딥링크·제휴 CTA는 운영
범위 밖** (과거 기획 §5 확장 항목에 있었지만 폐기).

- 광고 슬롯 컴포넌트: [src/components/AdSlot.astro](src/components/AdSlot.astro)
  (publisher ID·slot ID는 `.env` → `import.meta.env`로 주입, 코드 하드코딩 금지)
- 배치 위치 (정적·예측 가능, Auto Ads 미사용):
  1. **top 슬롯** — 요약(`answer-now`)과 본문(`prose`) 사이.
     사용자가 한 줄 답 읽고 본문 들어가기 전 자연스러운 휴식 지점.
  2. **bottom 슬롯** — FAQ 끝과 일반정보 고지 사이.
     FAQ가 비어 있으면 노출 안 함(출처 박스와 직접 인접하지 않도록).
  - **출처 박스 위아래는 광고 금지** (AD-04). 출처 신뢰감을 광고 인접으로
    훼손하지 않는다.
  - 홈/카테고리 랜딩에는 광고 슬롯을 두지 않는다 — 정보 밀도 우선.
- `public/ads.txt` 필수 — `google.com, pub-{PUBLISHER_ID}, DIRECT, f08c47fec0942fa0`
- 정책 가드 (compliance AD-*): 본문 최소 분량, 금지 카테고리 차단, 정책 문구
  필수, 광고 위치가 출처 박스/FAQ를 깨지 않도록 배치 규제
- 일반정보 고지(`disclaimer`)는 AdSense 정책상 의료·법률·금융 페이지에 권장 →
  현 시스템은 기본 true로 모든 글에 노출 중

`compliance` 룰 ID `AD-01`~`AD-05`로 자동 검증 — 자세히는
[compliance/checklist.md](compliance/checklist.md).

## Cloudflare Pages 빌드 설정

| 항목 | 값 |
|---|---|
| Build command | `npm run build` (`astro build`) |
| Build output | `dist` |
| Root directory | `/` (레포 루트) |

## docs/ 자료 인덱스 (재스캔 방지)

미래 세션이 docs/를 처음부터 다시 훑지 않도록, 각 파일의 용도와 어디에
인코딩됐는지 명시:

| 파일 | 성격 | 하네스 반영 상태 |
|---|---|---|
| [docs/기획서.md](docs/기획서.md) | 백엔드 마스터 기획 | 절대 원칙·IA·점수식·파이프라인·리스크 모두 본 CLAUDE.md와 에이전트 정의에 인코딩됨 |
| [docs/frontend-기획서.md](docs/frontend-기획서.md) | 프론트 디자인·페이지·GEO 기획 | 디자인 시스템·매핑·preview-first·출처 박스 불변 반영 완료 |
| [docs/바이브고팅 명령어 모음.txt](docs/바이브고팅%20명령어%20모음.txt) | Claude Code 슬래시 명령 카탈로그 | [WORKFLOW.md](WORKFLOW.md) + [.claude/settings.json](.claude/settings.json)에 적용된 것만 채택 |
| [docs/references/](docs/references/) (7) | 바이브코딩 방법론·하네스 엔지니어링·SEO 종합 | 핵심 룰만 발췌 (유사문서 회피 → brief-generator + compliance, 검색엔진 등록 → WORKFLOW §6.5). 미반영 항목은 "Phase 3 자동화" 또는 "운영자 분기 리뷰" 대상 |
| [docs/calculator-spec/](docs/calculator-spec/) (19) | 외부 프로젝트(calculatorhost) 계산기 스펙 | **mureobom 본문에서 사용하지 않음**. 수익화를 AdSense 단독으로 전환하면서 폐기. 폴더는 다른 프로젝트 참고용으로 보존 — 본 레포는 무관 |
| [docs/google-seo/](docs/google-seo/) (2) | Google SEO Fundamentals + 즉시 적용 템플릿 | OG/Twitter/Canonical → [src/layouts/Base.astro](src/layouts/Base.astro), robots.txt → [public/robots.txt](public/robots.txt), sitemap → [src/pages/sitemap.xml.ts](src/pages/sitemap.xml.ts), Article+BreadcrumbList+FAQPage @graph → [src/pages/\[cluster\]/\[slug\].astro](src/pages/[cluster]/[slug].astro), 제목/description 길이 검증 → [src/content/config.ts](src/content/config.ts) Zod, compliance M-01~M-09 |

새 docs/ 파일이 추가되면 본 표에 한 줄로 추가하고 어디에 인코딩됐는지 적어라.
인코딩되지 않은 파일은 미래 세션이 매번 다시 읽어야 하므로 비용이 든다.
