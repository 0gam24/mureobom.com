---
name: publish-daily
description: 오늘 발행 N편(기본 1) 자동 체인 — 토픽 선정부터 이미지·빌드·커밋·푸시까지. 하루 자동 1편 원칙, 추가 발행은 운영자 수동 지시(N 인자)로만
---

# publish-daily — 일일 발행 자동 체인 (기본 1편)

운영자가 `/publish-daily`(또는 `/publish-daily 2`)를 호출하거나 클라우드 루틴
`06 mureobom (07:00)`이 발화하면 오늘치 N편(기본 **1**)을 토픽 선정부터 커밋·푸시까지
한 번에 처리한다. 단계를 빼거나 순서를 바꾸지 마라.

> **왜 1편인가 (D-2026-09-02-1)**: 하루 3편 × 90일 동안 290편을 냈지만 Google 노출은
> 28일 99회·클릭 0(2026-08 GSC). Google 스팸 정책 "확장된 콘텐츠 악용"과 2026년 3·5·6월
> 업데이트가 정확히 이런 패턴(대량·유사 구조·차별화 부족)을 강등한다. 회복 조건은
> "적게, 그러나 이 글이 아니면 얻을 수 없는 정보"다. 잘못된 발행 1건이 발행 0건보다
> 사이트에 해롭다. **N>1은 운영자가 세션에서 명시 지시할 때만.**

## 날짜·시간 기준 — 항상 KST(Asia/Seoul)

- 오늘 KST 날짜: `TODAY_KST=$(date -u -d '+9 hours' +%F)` (클라우드 Linux·로컬 Windows Git
  Bash 양쪽 안전. `date +%F`·`TZ=Asia/Seoul date`는 함정). 프론트매터 `published`·`updated`,
  커밋 메시지, 보고서 날짜 모두 이 값.
- 자동 발화: 매일 **07:00 KST** = cron `0 22 * * *` UTC (한국은 서머타임 없음, 연중 고정).
  체인은 30~60분 걸리므로 완료는 07:30~08:00 KST. 그 전에 확인하면 "아직"이 정상.

## 0. 중복 실행 차단 (최우선)

```
grep -l "^published: $TODAY_KST" src/content/answers/*.md
```
결과가 N개 이상이면 오늘 몫은 이미 나갔다. **아무것도 발행하지 말고** "오늘 발행분이
이미 존재하여 종료"로 보고하고 끝낸다. 클라우드 실행이면 시작 전에
`git fetch origin main && git rebase origin/main`으로 최신 main 기준을 확보한 뒤 검사한다.

## 1. 필독

1. [CLAUDE.md](../../../CLAUDE.md) — 절대 원칙 4개 + 발행 캐던스
2. [docs/prompts/google-content-master-prompt-v4.md](../../../docs/prompts/google-content-master-prompt-v4.md)
   — 본문 품질 기준(writer·quality-gate가 따른다)
3. [docs/QUALITY_RUBRIC.md](../../../docs/QUALITY_RUBRIC.md) — 85점 게이트
4. [docs/GOOGLE_RECOVERY_PLAN.md](../../../docs/GOOGLE_RECOVERY_PLAN.md) — 왜 이렇게 하는지

## 2. 토픽 선정 (N개) + brief 확보

토픽 소스 우선순위:

```
1. approved brief 잔여분 (automation/briefs/{cluster}/*.brief.yaml, status: approved)
2. automation/topic-queue.json 상위 신규 — 단 큐가 stale(생성 7일 초과)이면 건너뜀
3. WebSearch 폴백 — 최근 14일 정부·공공기관(.go.kr/.or.kr) 보도자료·제도 변경·
   신청/납부 마감 임박 소재 중 4 클러스터에 맞고 검색 수요가 있을 것 2~3개
4. automation/ooda/calendar-2026-06.md (사실상 소진, 최후 폴백)
```

- **클러스터 배분(N=1)**: 요일 로테이션으로 정한다 — 월 loan · 화 tax · 수 support ·
  목 loan · 금 tax · 토 insurance · 일 loan (RPM 높은 loan·tax 우선, D-2026-06-11-3 유지).
  그날 클러스터에 통과 후보가 없으면 다음 순서 클러스터로 넘어간다. N>1이면 loan·tax부터.
- **카니발리제이션 검사(PART 33)**: 후보마다 `automation/briefs/_published_slugs.txt` 대조 +
  `grep -il "{핵심어}" src/content/answers/*.md`로 title·targetQuery·H2 대조. 같은 검색의도를
  이미 해결한 글이 있으면 기각(각도를 좁힌 롱테일은 허용). 통과 후보가 없으면 **0편으로
  종료해도 정상** — 보고에 기각 내역을 남긴다.
- **1차 출처 사전 확인**: 후보의 핵심 수치·기준일을 go.kr/or.kr 1차 출처에서 WebFetch로
  확인하지 못하면 그 후보를 버린다(fabrication-zero).
- **brief 초안**: 선정된 토픽에 brief가 없으면 `@brief-generator`로 초안 작성
  (`human_notes` 첫 줄 `차별화:` 필수). 파생 키워드는 `target_query`를 자연어로 다듬는다.
- **즉석 승인**: 운영자가 세션에서 "오늘 발행해"라고 지시했거나 클라우드 루틴 실행이면
  즉석 승인으로 간주해 `status: approved`로 바꾸되, **어떤 brief를 즉석 승인했는지 보고에
  명시**한다.
- **지식iN 가드**: 큐 키워드는 신호일 뿐. 본문은 항상 공식 1차 출처로 원본 작성.

## 3. 에이전트 직렬 체인 (편당)

```
@researcher    → automation/research/{cluster}/{slug}.research.yaml (gaps 비어야 진행)
@writer        → src/content/answers/{slug}.md + public/diagrams/{slug}.svg
                 (docs/prompts/google-content-master-prompt-v4.md 적용)
@quality-gate  → 85점 게이트. REVISE면 writer 1회 수정 후 재채점.
                 재채점 85 미만 또는 KILL이면 해당 편 폐기(오늘 0편, 대체 글 급조 금지)
@geo           → faq(후속 질문만)·summary 다듬기·internalLinks 실존 검증
(이미지 생성 — 아래 4단계)
@compliance    → 통과 시 brief status: published + _published_slugs.txt 추가
```

effort는 WORKFLOW.md §3 표 그대로(researcher·writer·quality-gate·compliance xhigh, geo medium).
서브에이전트 spawn이 거부되는 환경이면 general-purpose 에이전트에 해당
`.claude/agents/*.md` 전문을 프롬프트로 담아 동일 역할을 대행시킨다.

## 4. 대표 이미지(WebP)·OG 생성 (compliance 직전)

```
node   scripts/gen_post_hero.mjs --slug {slug}    # public/img/{slug}.webp 1200×900 + frontmatter hero:
python scripts/gen_post_og.py    --slug {slug}    # public/og/{slug}.png 1200×630 + frontmatter image:
```

- hero WebP는 본문 첫 인포그래픽 SVG를 래스터화한 것 — 검색 결과 썸네일(og:image·
  Article.image·primaryImageOfPage·이미지 사이트맵·RSS enclosure)이 된다. 파일이 5KB 미만이거나
  실패하면 SVG(텍스트 크기·viewBox)를 고쳐 재생성. compliance V-05가 존재를 검사한다.
- 두 스크립트는 레포 동봉 폰트(scripts/fonts)만 쓰므로 로컬·클라우드 출력이 같다.
  `--all`은 전체 재생성이므로 발행 체인에서 쓰지 마라.
- 폐기된 편의 webp/png/svg/md는 커밋 전에 삭제한다(고아 파일 금지).

## 5. llms.txt 재생성

```
python scripts/gen_llms_posts.py
```

## 6. 빌드 검증

```
npm run build
```
Zod(sources min 1, title/summary 길이, hero/image 경로) 위반이면 여기서 실패한다.
실패 시 고치고 재빌드 — 빌드 실패 상태로 7단계에 가지 마라.

## 7. 커밋·푸시

```
git add src/content/answers/{slug}.md public/diagrams/{slug}*.svg public/img/{slug}.webp \
        public/og/{slug}.png public/llms.txt automation/briefs/{cluster}/{slug}.brief.yaml \
        automation/briefs/_published_slugs.txt
git commit -m "feat: 1편 발행 (KST $TODAY_KST) — {cluster}/{slug}"
git fetch origin main && git rebase origin/main && git push origin HEAD:main
```
`git add .` 금지. force push·main 외 브랜치·기존 글 삭제 금지. 커밋 메시지 끝에
`Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` 한 줄.

## 8. 배포 확인 + 보고

push 후 Cloudflare Pages가 자동 배포한다(2~5분). `curl -sI https://mureobom.com/{cluster}/{slug}/`
가 200이면 완료. 클라우드 환경의 네트워크 정책이 mureobom.com을 차단하면 우회하지 말고
"네트워크 정책으로 프로덕션 확인 불가, 푸시는 완료"로 보고한다.

```
published 1편:
- https://mureobom.com/{cluster}/{slug}/ — {title}
  선정 근거: {토픽 소스(brief/큐/WebSearch)} · 차별화: {한 줄} · 구조 TYPE {X}
  게이트: quality-gate {점수} · compliance OK · build OK · hero {KB} · og OK
(0편이면: 기각 후보와 사유 — 카니발리제이션/출처 미확인/게이트 KILL)
```

## 절대 금지

- 하루 자동 1편 초과 (N>1은 운영자 세션 명시 지시로만)
- 오늘 발행분이 이미 있는데 또 발행 (§0)
- quality-gate REVISE 2회 이상, KILL 후 대체 글 급조
- 빌드 실패 상태 커밋, `git add .`, force push
- 지식iN 원문/URL 유입 (PreToolUse 훅이 차단하지만 시도 자체 금지)
- `_published_slugs.txt`에 있는 슬러그 재발행
- 확인 안 된 수치·조문·URL 작성 (연구 bundle 밖 출처 금지)
