---
description: 단건 품질 검수 (Phase 0부터 사용). 글 경로를 받아 quality-gate 판정을 출력하거나, --hygiene으로 애드센스 심사 위생을 점검한다.
---

인자: $ARGUMENTS

## --hygiene 인 경우
docs/ADSENSE_REVIEW_CHECKLIST.md를 기준으로 리포 전체를 점검하라.
필수 페이지 존재, 얇은 글(300자 미만) 목록, 깨진 내부링크, sitemap/robots 상태를 확인하고
체크리스트 형식의 점검 리포트와 보강 우선순위를 출력하라. 파일을 수정하지는 마라.

## 글 경로인 경우
해당 글에 대해 quality-gate 서브에이전트를 호출해 docs/QUALITY_RUBRIC.md 기준 채점을 받아라.
판정 JSON과 함께, REVISE인 경우 issues를 사람이 고치기 쉽게 위치별로 정리해 보여줘라.
글을 직접 수정하지 마라 — Phase 0에서는 운영자가 직접 고친다.
