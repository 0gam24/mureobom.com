#!/usr/bin/env python3
"""GSC CSV 내보내기 파서.

운영자가 GSC '실적 → 내보내기 → CSV 다운로드'로 받은 ZIP을 분석한다.
인증 셋업이 불가능하거나 번거로울 때의 우회 경로.

사용:
  1) GSC → 실적 → 3개월(또는 28일) → 우상단 '내보내기' → 'CSV 다운로드'
  2) 다운받은 ZIP을 다음 경로에 저장: automation/discovery/gsc-export.zip
     (또는 ZIP을 풀어서 automation/discovery/gsc-export/ 폴더에 CSV들을 둠)
  3) python automation/scripts/gsc_csv_parser.py

GSC ZIP 안의 파일 (한국어/영어 UI 자동 감지):
  - Queries.csv         (검색어)
  - Pages.csv           (페이지)
  - Devices.csv         (디바이스)
  - Countries.csv       (국가)
  - Search appearance.csv
  - Dates.csv

산출:
  automation/ooda/gsc-snapshot-latest.json
  automation/ooda/gsc-summary-latest.md
"""
from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DISCOVERY_DIR = REPO_ROOT / "automation" / "discovery"
OUT_DIR = REPO_ROOT / "automation" / "ooda"

# 한국어/영어 헤더 매핑 (어떤 GSC UI로 받든 처리)
HEADER_MAP = {
    "상위 검색어": "key", "Top queries": "key",
    "상위 페이지": "key", "Top pages": "key",
    "기기": "key", "Device": "key",
    "국가": "key", "Country": "key",
    "날짜": "key", "Date": "key",
    "검색 모양": "key", "Search appearance": "key",
    "클릭수": "clicks", "Clicks": "clicks",
    "노출수": "impressions", "Impressions": "impressions",
    "CTR": "ctr",
    "게재순위": "position", "Position": "position",
}

FILENAME_MAP = {
    "queries": ["Queries.csv", "검색어.csv", "Search queries.csv"],
    "pages": ["Pages.csv", "페이지.csv"],
    "devices": ["Devices.csv", "기기.csv"],
    "countries": ["Countries.csv", "국가.csv"],
    "dates": ["Dates.csv", "날짜.csv"],
}


def load_csv_text(text: str) -> list[dict]:
    """헤더 매핑 적용해 표준 키 dict 리스트로 변환."""
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    header = [HEADER_MAP.get(h.strip(), h.strip()) for h in rows[0]]
    out = []
    for r in rows[1:]:
        d = dict(zip(header, r))
        out.append(d)
    return out


def parse_pct(s: str) -> float:
    """'2.7%' 또는 '0.027' → 0.027"""
    if not s:
        return 0.0
    s = s.strip().replace("%", "").replace(",", "")
    try:
        v = float(s)
        return v / 100 if "%" in str(s) or v > 1 else v
    except ValueError:
        return 0.0


def parse_int(s: str) -> int:
    if not s:
        return 0
    try:
        return int(str(s).replace(",", "").strip())
    except ValueError:
        return 0


def parse_float(s: str) -> float:
    if not s:
        return 0.0
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return 0.0


def normalize(rows: list[dict]) -> list[dict]:
    """공통 숫자 정규화. CTR은 0~1 스케일로 통일."""
    out = []
    for r in rows:
        out.append({
            "key": r.get("key", "").strip(),
            "clicks": parse_int(r.get("clicks", "0")),
            "impressions": parse_int(r.get("impressions", "0")),
            "ctr": parse_pct(r.get("ctr", "0")),
            "position": parse_float(r.get("position", "0")),
        })
    return out


def load_from_zip(zip_path: Path) -> dict[str, list[dict]]:
    """ZIP 안의 CSV들을 dimension별로 로드."""
    result: dict[str, list[dict]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        for dim, candidates in FILENAME_MAP.items():
            matched = next((n for n in names if any(n.endswith(c) for c in candidates)), None)
            if matched:
                with zf.open(matched) as f:
                    text = f.read().decode("utf-8-sig", errors="replace")
                    result[dim] = normalize(load_csv_text(text))
    return result


def load_from_folder(folder: Path) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for dim, candidates in FILENAME_MAP.items():
        for cand in candidates:
            p = folder / cand
            if p.exists():
                text = p.read_text(encoding="utf-8-sig", errors="replace")
                result[dim] = normalize(load_csv_text(text))
                break
    return result


def short_url(u: str) -> str:
    return (
        u.replace("https://mureobom.com", "")
        .replace("https://www.mureobom.com", "")
        or "/"
    )


def fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def fmt_pos(x: float) -> str:
    return f"{x:.1f}"


def render_markdown(data: dict[str, list[dict]]) -> str:
    lines: list[str] = []
    lines.append("# GSC 스냅샷 — CSV 파싱")
    lines.append("")
    lines.append("> 출처: GSC '실적 → 내보내기' CSV ZIP 직접 파싱.")
    lines.append("> 기간은 CSV 다운로드 시 GSC에서 선택한 기간(보통 28일 또는 3개월).")
    lines.append("")

    queries = data.get("queries", [])
    pages = data.get("pages", [])

    if queries:
        total_clicks = sum(r["clicks"] for r in queries)
        total_imp = sum(r["impressions"] for r in queries)
        avg_pos = (
            sum(r["position"] * r["impressions"] for r in queries) / total_imp
            if total_imp else 0
        )
        ctr = total_clicks / total_imp if total_imp else 0
        lines.append("## 총계 (검색어 기준 합산)")
        lines.append(f"- 클릭: **{total_clicks}**")
        lines.append(f"- 노출: **{total_imp}**")
        lines.append(f"- CTR: **{fmt_pct(ctr)}**")
        lines.append(f"- 가중 평균 게재순위: **{fmt_pos(avg_pos)}**")
        lines.append("")

    if queries:
        lines.append("## 상위 검색어 (Top 15)")
        lines.append("| 검색어 | 클릭 | 노출 | CTR | 순위 |")
        lines.append("|---|---|---|---|---|")
        for r in queries[:15]:
            lines.append(
                f"| {r['key']} | {r['clicks']} | {r['impressions']} "
                f"| {fmt_pct(r['ctr'])} | {fmt_pos(r['position'])} |"
            )
        lines.append("")

    if pages:
        lines.append("## 상위 페이지 (Top 15)")
        lines.append("| 페이지 | 클릭 | 노출 | CTR | 순위 |")
        lines.append("|---|---|---|---|---|")
        for r in pages[:15]:
            p = short_url(r["key"])
            lines.append(
                f"| {p} | {r['clicks']} | {r['impressions']} "
                f"| {fmt_pct(r['ctr'])} | {fmt_pos(r['position'])} |"
            )
        lines.append("")

        # 트랙 2 후보 — 노출 ≥10 + 클릭 0
        candidates = [
            r for r in pages if r["clicks"] == 0 and r["impressions"] >= 10
        ]
        lines.append("## 트랙 2(재공유) 후보 — 노출 ≥10 + 클릭 0")
        if candidates:
            lines.append("| 페이지 | 노출 | 순위 |")
            lines.append("|---|---|---|")
            for r in candidates[:20]:
                lines.append(
                    f"| {short_url(r['key'])} | {r['impressions']} | {fmt_pos(r['position'])} |"
                )
        else:
            lines.append("- 해당 없음 (모든 노출 페이지에 클릭 ≥1)")
        lines.append("")

        # 제목/summary 개선 후보 — 노출 50+ & CTR < 1.5%
        weak_ctr = [
            r for r in pages
            if r["impressions"] >= 50 and r["ctr"] < 0.015 and r["clicks"] > 0
        ]
        lines.append("## 제목·summary 개선 후보 — 노출 ≥50 + CTR <1.5%")
        if weak_ctr:
            lines.append("| 페이지 | 노출 | 클릭 | CTR | 순위 |")
            lines.append("|---|---|---|---|---|")
            for r in weak_ctr[:15]:
                lines.append(
                    f"| {short_url(r['key'])} | {r['impressions']} | {r['clicks']} "
                    f"| {fmt_pct(r['ctr'])} | {fmt_pos(r['position'])} |"
                )
        else:
            lines.append("- 해당 없음")
        lines.append("")

    devices = data.get("devices", [])
    if devices:
        lines.append("## 디바이스 분포")
        lines.append("| 디바이스 | 클릭 | 노출 | CTR |")
        lines.append("|---|---|---|---|")
        for r in devices:
            lines.append(
                f"| {r['key']} | {r['clicks']} | {r['impressions']} | {fmt_pct(r['ctr'])} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    zip_path = DISCOVERY_DIR / "gsc-export.zip"
    folder_path = DISCOVERY_DIR / "gsc-export"

    if zip_path.exists():
        data = load_from_zip(zip_path)
        source = str(zip_path)
    elif folder_path.exists() and folder_path.is_dir():
        data = load_from_folder(folder_path)
        source = str(folder_path)
    else:
        sys.exit(
            f"[gsc_csv_parser] 입력 파일 없음. 다음 중 하나에 GSC ZIP 또는 CSV들을 두세요:\n"
            f"  - {zip_path}\n"
            f"  - {folder_path}/Queries.csv, Pages.csv, ..."
        )

    if not data:
        sys.exit(f"[gsc_csv_parser] {source} 에서 CSV를 찾지 못했습니다.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "gsc-snapshot-latest.json").write_text(
        json.dumps({"source": "csv", "data": data}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "gsc-summary-latest.md").write_text(
        render_markdown(data), encoding="utf-8"
    )

    print(f"[gsc_csv_parser] source: {source}")
    print(f"[gsc_csv_parser] dimensions loaded: {list(data.keys())}")
    print(f"[gsc_csv_parser] wrote {OUT_DIR / 'gsc-snapshot-latest.json'}")
    print(f"[gsc_csv_parser] wrote {OUT_DIR / 'gsc-summary-latest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
