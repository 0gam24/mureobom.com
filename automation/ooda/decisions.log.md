# Decisions Log — 물어봄 Macro OODA

> 운영자가 매주 Macro OODA에서 채택한 결정을 한 항목씩 시간 역순으로 기록.
> ADR(Architecture Decision Record) lite 형식. 결정마다 30초~2분 투자.
> 6개월 후 "이건 왜 이렇게 됐지?" 미스터리 방지가 목적.
>
> 양식: 새 항목은 **맨 위에** (역시간순). 항목 ID는 `D-{YYYY-MM-DD}-{N}`.

---

## 양식 (복사용)

```
## D-{YYYY-MM-DD}-{N}: {한 줄 결정 제목}

- **층위**: Macro 주간 / Macro 월간 / 긴급(즉시)
- **변경**: {파일·룰·가중치 1~3줄}
- **근거 (Orient)**: {observations/{YYYY-WW}.md 어느 섹션의 어느 수치}
- **기대 효과**:
  - 1주: {지표}
  - 1개월: {지표}
- **롤백 기준**: {N주 후 효과 없으면 revert}
- **연관 PR**: #{번호}
- **Outcome (1주 후 작성)**:
- **Outcome (1개월 후 작성)**:
```

---

## D-2026-05-19-1: 본 로그 시작

- **층위**: 초기 셋업
- **변경**: [OODA.md](../../OODA.md) + [observations.template.md](observations.template.md) + 본 로그 신설.
- **근거 (Orient)**: docs/references/04-통합-3레이어-OS.md의 외부·실행·제어 3레이어
  각각에 명시적 의사결정 루프 부재. 향후 결정이 메모리에만 남아 6개월 후 미스터리 위험.
- **기대 효과**:
  - 1주: 첫 observations 스냅샷 작성 (Phase 1 운영 진입 시)
  - 1개월: 결정 ≥ 4개 누적 → 가중치·룰 추세 비교 가능
- **롤백 기준**: 4주 동안 결정 0건이면 OODA 캐던스 자체 재설계
- **연관 PR**: (초기 하네스 일괄)
- **Outcome (1주 후 작성)**: (대기)
- **Outcome (1개월 후 작성)**: (대기)
