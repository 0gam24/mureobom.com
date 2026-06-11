# WORKFLOW.md — 운영자 슬래시 명령어 맵

물어봄 콘텐츠 파이프라인 각 단계에서 어떤 Claude Code 슬래시 명령어를 칠지.
시간 흐름 순. 처음 1회만 쓰는 항목엔 (1회), 매번 쓰는 항목엔 (반복).

## 0. 초기 1회 세팅

순서가 중요 — 디자인 톤을 먼저 잡고 Astro에 옮긴다 (frontend-기획서 §6).

```
0-a. preview.html을 브라우저로 열어 톤 확인 (폰트 weight·여백·색감)
0-b. src/styles/tokens.css 미세조정 (필요 시 hex/clamp 값만)
0-c. npm create astro@latest . (또는 수동 package.json) → npm install
0-d. npm run dev → 더미 md 2개로 라우트 동작 확인
0-e. git init → 첫 커밋
0-f. Cloudflare Pages 연결 (build: astro build, output: dist)
```

| 명령 | 용도 |
|---|---|
| `/doctor` (1회) | 설치·환경 진단 |
| `/permissions` (1회) | [.claude/settings.json](.claude/settings.json) 확인. 이미 화이트/블랙리스트 + 훅 설정됨 |
| `/agents` (1회) | [.claude/agents/](.claude/agents/) 6개 서브에이전트 로드 확인 |
| `/memory` (수시) | [CLAUDE.md](CLAUDE.md) / 오토메모리 편집 |

## 1. 매일 — 토픽 큐 검토

GitHub Actions cron이 매일 KST 06:00 [topic-scanner.yml](.github/workflows/topic-scanner.yml)을 돌려
`bot/topic-queue` 브랜치로 PR을 연다.

| 명령 | 용도 |
|---|---|
| `/resume` | 어제 작업하던 세션 재개 |
| `/review {PR번호}` | bot/topic-queue PR 로컬 검토 |
| `/diff` | `automation/topic-queue.json` 변경분 인터랙티브 뷰 |

## 2. brief 초안 생성 → 사람 15분 검수

큐 상위 항목 N개를 선택해 brief 초안을 만든다.

```
@brief-generator automation/topic-queue.json[0]번 항목으로 초안 작성
```

| 명령 | 용도 |
|---|---|
| `/agents brief-generator` | 또는 위처럼 @-멘션으로 직접 호출 |
| `/effort medium` | brief는 구조 변환이라 medium 충분 |
| `/diff` | 사람이 brief 검토 — `must_cover` 수정, `required_sources` 보강 |
| `/rewind` | brief 잘못 작성됐을 때 체크포인트 복귀 |

brief의 `status:`를 `draft` → `approved`로 직접 편집하면 무인 단계 진입.

## 3. 무인 파이프라인 (5 에이전트 직렬)

```
@researcher → @writer → @quality-gate(85점 게이트, REVISE 1회) → @geo → @compliance
```

quality-gate가 REVISE 판정하면 writer가 1회만 수정 후 재채점. 재채점 85 미만이면 KILL.

| 명령 | 권장 effort | 사유 |
|---|---|---|
| `/effort xhigh` | researcher 호출 전 | 출처 매핑·gap 분석에 추론 필요 |
| `/effort xhigh` | writer 호출 전 | Opus 4.7 코딩 기본값. 본문 품질의 핵심 |
| `/effort xhigh` | quality-gate 호출 전 | 레드팀 채점 + 출처 WebFetch 실확인에 보수적 추론 필요 |
| `/effort medium` | geo 호출 전 | FAQ JSON-LD는 기계적 |
| `/effort xhigh` | compliance 호출 전 | 차단 판단에 보수적 추론 필요 |

`compliance`가 차단하면 `<!-- BLOCKED -->` 마커가 남고 PR 머지 안 됨.

| 명령 | 용도 |
|---|---|
| `/background` | research가 길어지면 백그라운드로 분리 |
| `/tasks` | 백그라운드 작업 상태 확인 |
| `/diff` | 각 에이전트 산출물 검토 |

## 4. 병렬 발행 (MVP 20글 한 번에)

4 카테고리 × 5글을 한 번에 처리할 때:

| 명령 | 용도 |
|---|---|
| `/batch` (스킬) | 5~30개 단위로 워크트리 분리해 병렬 실행. 클러스터별 분기 추천 |
| `/branch` | 클러스터별 brief 동시 작업 분기 |

## 5. 배포 전 검수

| 명령 | 용도 | 호출 시점 |
|---|---|---|
| `/simplify` (스킬) | 본문 중복·과잉 제거 후 자동 수정 | writer 산출 직후 |
| `/review` | auto-PR 로컬 리뷰 | compliance OK 직후 |
| `/security-review` | 보안 취약점 분석 | `automation/scripts/topic_scanner.py`·hooks 변경 시 |
| `/ultrareview` (사용자 트리거) | 클라우드 멀티에이전트 심층 리뷰 | 첫 auto-merge 적용 전 1회 권장 |
| `/diff` | 최종 변경 인터랙티브 뷰 | merge 직전 |

## 6. 문제 발생

| 상황 | 명령 |
|---|---|
| compliance가 차단 → brief 수정 후 재시도 | `/rewind` (체크포인트 복귀) |
| API 한도 의심 | `/debug` (스킬, 디버그 로깅 후 분석) |
| 에이전트 산출 이상 | `/feedback` (세션 컨텍스트 첨부 리포트) |

## 6.5. 첫 발행 직후 검색엔진 등록 + AdSense 신청 (Phase 1~2 운영, 1회)

### 사전 점검 (등록 전 라이브 확인)

| 점검 | 명령/URL |
|---|---|
| robots.txt 라이브 | `curl https://mureobom.com/robots.txt` → 200 + Sitemap 라인 |
| sitemap.xml 라이브 | `curl https://mureobom.com/sitemap.xml` → 200 + 모든 URL 포함 |
| Article JSON-LD 노출 | https://search.google.com/test/rich-results 에서 발행 글 1개 검증 |
| Open Graph 미리보기 | https://www.opengraph.xyz 또는 페이스북/카카오 디버거 |
| `astro.config.mjs`의 `site` | `https://mureobom.com` 으로 설정해야 sitemap·canonical이 절대 URL |
| **og-default.png 라이브** | `public/og-default.png` 자동 생성됨 (1200×630). 브랜드 변경 시 `python scripts/gen_og_default.py` 재실행 |
| **apple-touch-icon.png 라이브** | `public/apple-touch-icon.png` 180×180 자동 생성됨 (`scripts/gen_apple_touch_icon.py`) |
| **AdSense env 설정** | `PUBLIC_ADSENSE_CLIENT`·`PUBLIC_ADSENSE_SLOT_TOP`·`_BOTTOM` 셋 다 설정해야 광고 노출. 셋 중 하나라도 미설정이면 AdSlot은 아무것도 렌더하지 않음 (개발 placeholder 보려면 `PUBLIC_ADSENSE_DEBUG=1`) |

### 검색엔진

| 항목 | URL | 액션 |
|---|---|---|
| Google Search Console | https://search.google.com/search-console | 도메인 등록 → DNS TXT 또는 `PUBLIC_GOOGLE_SITE_VERIFICATION` env 메타로 검증 → `sitemap.xml` 제출 |
| Naver Search Advisor | https://searchadvisor.naver.com | 사이트 등록 → `PUBLIC_NAVER_SITE_VERIFICATION` env 메타로 검증 → `sitemap.xml` 제출 → 1~3건 수동 수집 요청 |
| Bing Webmaster Tools | https://www.bing.com/webmasters | Google에서 가져오기로 자동 |

메타 태그는 [src/layouts/Base.astro](src/layouts/Base.astro)가 env 값이 있을 때만 자동 삽입.
하드코딩 금지 ([compliance/checklist.md](compliance/checklist.md) AD-07과 같은 정책).

### Google AdSense (수익화 단독 채널)

| 순서 | 항목 | 액션 |
|---|---|---|
| 1 | 사전 조건 | 20글 이상 발행 + Cloudflare Pages 안정 운영 + `/about`·`/privacy` 페이지 + `public/ads.txt` 존재 |
| 2 | 가입 | https://adsense.google.com → 사이트 mureobom.com 추가 |
| 3 | 사이트 검증 | AdSense 코드를 [src/layouts/Base.astro](src/layouts/Base.astro)에 추가 → 이미 `PUBLIC_ADSENSE_CLIENT` env 있으면 자동 주입. Cloudflare Pages 환경변수 UI에서 값 설정 후 재배포 |
| 4 | ads.txt | [public/ads.txt](public/ads.txt)의 `PUBLISHER_ID`를 발급받은 ID로 치환 |
| 5 | 검토 대기 | 보통 1~14일. compliance AD-* 룰 통과 사이트는 거의 자동 승인 |
| 6 | 슬롯 생성 | in-article ad unit 2개 (top, bottom) 만들고 slot ID를 `PUBLIC_ADSENSE_SLOT_TOP`/`_BOTTOM`에 설정 |
| 7 | compliance 격상 | AD-01·AD-07을 경고 → 차단으로 격상 ([compliance/checklist.md](compliance/checklist.md) §7) |

### 승인 직후 (D-Day, 15분)

AdSense 승인 메일 수신 당일 아래 5개를 한 번에 처리한다. 순서대로 15분.

1. **Auto ads OFF 확인** — AdSense 콘솔 → 사이트 → mureobom.com → Auto ads가
   꺼져 있는지 확인. 우리는 정적 슬롯 2개(top/bottom)만 운영 (CLAUDE.md 수익화 §).
2. **라이브 글 1개 슬롯 실게재 확인** — 발행 글 아무거나 열어 top/bottom 슬롯에
   광고가 실제 렌더되는지 확인 (빈 슬롯이면 env 3종 + 재배포 점검).
3. **Privacy & messaging GDPR 기본 메시지 게시** — AdSense 콘솔 → Privacy &
   messaging → 유럽 규정 메시지 '게시'. 코드 변경 없음 (콘솔 CMP 사용).
4. **GA4-AdSense 연동** — GA4 관리 → 제품 링크 → AdSense 링크 추가.
   페이지별 수익 리포트가 주간 OODA §3 입력이 된다.
5. **지급 정보 등록** — AdSense 지급 → 수취인 정보 + 은행 계좌 등록
   (등록 지연 시 기준액 도달해도 지급 보류).

### 네이버 SEO 핵심
출처 신뢰도(C-Rank), 정보성(D.I.A.), 유사문서 회피(D.I.A.+).
유사문서 회피는 brief-generator의 `차별화:` 필드 + compliance 검사로 1차 처리.

## 6.9. 주간/월간 OODA 회고 (Macro 루프)

[OODA.md](OODA.md)의 Macro 층위. 발행 단계 진입 후 매주 1회 반복.

### 주간 (월요일 09:00 권장, 30~45분)

```
1. observations.template.md 복사 →
   automation/ooda/observations/{YYYY-WW}.md
   섹션 1~6 채움 (Search Console + AdSense + 큐 + compliance 차단 로그)
2. §7 Orient — 패턴/이상치 5~10줄
3. §8 Decide — 결정 후보 1~5개 작성
4. 채택한 결정 → automation/ooda/decisions.log.md 맨 위에 항목 추가
5. 변경 PR ("ooda-week-{YYYY-WW}" 브랜치) 본문에 decisions 항목 링크
6. 머지
```

운영자가 쓸 슬래시 명령: `/resume` → `/diff` (메트릭 PR 검토) →
`/branch ooda-week-{YYYY-WW}` → `/effort xhigh` (가중치 튜닝 판단) → `/review`.

### 월간 (월말, 1시간)

- 직전 4주 decisions의 Outcome 채움
- 누적 추세: scoring 가중치 v3 필요? compliance 룰 격상/격하?
- 1개월 단위 결정 (시드 갱신·클러스터 재배치·AdSense 슬롯 A/B)

### 긴급 (즉시)

- API 한도 ≥70% 도달, 컴플라이언스 정책 변경, 발행 차단률 급등 시
- 정규 캐던스 기다리지 말고 `긴급` 라벨로 decisions 항목 추가

## 7. 세션 간 이동

| 상황 | 명령 |
|---|---|
| 새 카테고리 작업 시작 | `/clear` (프로젝트 메모리 유지) |
| 어제 작업 이어서 | `/resume {ID}` |
| 같은 brief를 다른 톤으로 실험 | `/branch` |

## ultrathink 키워드

명령이 아닌 키워드. 다음 상황의 프롬프트에 한 단어로 박는다:

- compliance 차단 사유가 모호할 때 ("ultrathink 이 본문에서 어떤 룰 위반인지 정확히 짚어")
- 점수 가중치 튜닝 결정 ("ultrathink 1주차 데이터로 본 가중치 조정안")
- IA·클러스터 분리/통합 결정

세션 비용 효율을 위해 일상 호출엔 쓰지 말 것.

## 안 쓰는 명령 (이 프로젝트에 불필요)

`/mcp` (외부 서버 없음), `/loop` (cron이 대체), `/teleport`·`/remote-control`
(1인 개발), `/btw`·`/goal` (오버킬), `/claude-api` (API 앱 아님).

## 핵심 라인

```
일상:  /resume → /diff → @brief-generator → /diff → status:approved
       → @researcher → @writer → /simplify → @quality-gate → @geo → @compliance
       → /review → /diff → merge
주간:  /batch (병렬 발행) + /ultrareview (1회 심층)
긴급:  /rewind → /debug → /feedback
```
