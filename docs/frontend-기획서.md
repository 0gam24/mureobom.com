# 물어봄 프론트엔드 기획서

> 스택: Astro 6.2 + Cloudflare Pages (머니룩 인프라 재사용)
> 컨셉: **물(신뢰·차분) + 봄(친근·새싹)** — 금융 주제의 신뢰감과
> 질문형 사이트의 친근함을 동시에 잡는 에디토리얼 톤.

---

## 1. 디자인 시스템

| 항목 | 값 | 의도 |
|---|---|---|
| 배경 | 따뜻한 크림 `#FBF7F0` | AI슬롭 흰배경 회피, 종이 같은 신뢰감 |
| 텍스트 | 워터잉크 `#1A2B2A` | 순검정 대신 차분한 잉크 |
| 시그니처 | 워터틸 `#0E7C72` | 브랜드 "물", 신뢰+청량 |
| 헤드라인 | 명조 `Gowun Batang` | 한국어 정보·신뢰 톤, 흔한 sans 회피 |
| 본문/UI | `IBM Plex Sans KR` | 가독성 + Pretendard 식상함 회피 |
| 라인하이트 | 1.85 | 한국어 장문 가독성 |

시그니처 모티프: 로고의 "봄"을 틸로, 옆에 새싹 글리프(`.sprout`). 카드 배경에 옅은 "?" 텍스처 — 질문형 사이트 정체성을 은은하게 반복.

토큰은 `src/styles/tokens.css` 단일 소스. 컴포넌트에서 색·간격 하드코딩 금지.

---

## 2. 페이지 인벤토리

| 라우트 | 파일 | 역할 |
|---|---|---|
| `/` | `pages/index.astro` | 히어로 + 4카테고리 + 최신 질문 9 |
| `/{cluster}` | `pages/[cluster]/index.astro` | 카테고리 랜딩(tax/support/loan/insurance) |
| `/{cluster}/{slug}` | `pages/[cluster]/[slug].astro` | 질문 상세(답+출처+FAQ) |

`getStaticPaths`로 4개 클러스터·전체 글 정적 생성 → Cloudflare Pages 정적 배포.

---

## 3. 컴포넌트

- `Base.astro` — 폰트 로드, 메타, 헤더/푸터, JSON-LD 슬롯, 일반정보 고지
- `QuestionCard.astro` — 홈/목록 공용 카드(태그·질문·요약·날짜·? 텍스처)
- 상세 페이지 내장: 핵심답 박스 → 본문 → **공식 출처 박스** → FAQ 아코디언 → 고지

핵심 신뢰 장치: "확인한 공식 자료" 박스를 본문 직후 고정 배치. 출처 0건이면 콘텐츠 스키마(`min(1)`)가 빌드를 막음 → 원본성 가드가 프론트에서도 강제됨.

---

## 4. 데이터 바인딩 (백엔드 → 프론트 일관성)

`src/content/config.ts`의 컬렉션 스키마가 brief.yaml 승인 필드와 1:1:

```
brief.yaml(approved) → 작성 에이전트 → src/content/answers/*.md (frontmatter)
  title / cluster / targetQuery / searchIntent / summary
  / updated / sources(min1) / faq[] / internalLinks / disclaimer
→ [slug].astro 가 FAQ를 FAQPage JSON-LD로 자동 출력 (GEO)
```

새 글 추가 = 마크다운 1개 추가 → 빌드 → 카테고리·홈·사이트맵 자동 반영. 무인 파이프라인과 그대로 맞물림.

---

## 5. GEO / SEO 내장

- 상세 페이지 `faq[]` → `FAQPage` JSON-LD 자동 생성(리치결과·AI 인용)
- 공식 출처 명시 노출 → E-E-A-T 신호
- 정적 생성 + Cloudflare 엣지 → 코어 웹 바이탈 유리
- (확장) `llms.txt`·사이트맵은 머니룩 GEO 스크립트 재사용

---

## 6. 바이브코딩 작업 순서

1. `npm create astro@latest` → 빈 프로젝트, `src/` 에 본 스캐폴드 복사
2. `@astrojs/...` content collections 활성 확인, `tokens.css` 임포트 경로 점검
3. `src/content/answers/`에 예시 글 2~3개(brief 예시 기반) 넣고 `npm run dev`
4. `preview.html`과 대조하며 톤 미세조정(폰트 weight, 여백)
5. Cloudflare Pages 연결 → 빌드 명령 `astro build`, 출력 `dist`
6. 백엔드 `topic_scanner` → brief → 작성 에이전트가 `answers/*.md` 생성하도록 연결

> `preview.html`을 브라우저로 먼저 열어 디자인 방향부터 확정한 뒤 Astro로 옮기는 걸 권장. 톤이 마음에 안 들면 토큰만 바꿔도 전체가 바뀜.
