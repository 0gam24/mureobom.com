#!/usr/bin/env python3
"""GSC(Google Search Console) Search Analytics 자동 수집기.

운영 흐름:
  1) Macro OODA Observe — 매주 GSC 클릭/노출/CTR/순위를 스냅샷으로 저장
  2) 트랙 2(재공유) 우선순위 — "노출만 있고 클릭 0인 페이지" 자동 추출
  3) observations/{YYYY-WW}.md §2(트래픽) 셀의 1차 소스가 됨

산출:
  automation/ooda/gsc-snapshot-latest.json   — 전체 응답 (top_queries, top_pages, devices)
  automation/ooda/gsc-summary-latest.md      — observations에 붙여넣기용 마크다운

인증:
  - 우선: 환경변수 GSC_CREDS_JSON에 서비스 계정 키 JSON 문자열
  - 폴백: 로컬 파일 GSC_CREDS_FILE (기본 'gsc-creds.json', .gitignore 처리됨)
  - 서비스 계정 이메일을 GSC 속성에 '사용자 관리'에서 권한 부여 필수

환경변수:
  GSC_SITE_URL  속성 식별자. 도메인 속성이면 'sc-domain:mureobom.com',
                URL 속성이면 'https://mureobom.com/' (기본: sc-domain:mureobom.com)
  GSC_DAYS      집계 기간 일수 (기본 28)
  GSC_TOP_N     상위 N개 행 (기본 25)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SITE_URL = os.environ.get("GSC_SITE_URL", "sc-domain:mureobom.com")
DAYS = int(os.environ.get("GSC_DAYS", "28"))
TOP_N = int(os.environ.get("GSC_TOP_N", "25"))
CREDS_FILE = os.environ.get("GSC_CREDS_FILE", "gsc-creds.json")
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
OUT_DIR = REPO_ROOT / "automation" / "ooda"


def _load_user_creds(info: dict):
    """ADC/OAuth user credential을 그대로 받아 자동 갱신.
    필수 키: refresh_token, client_id, client_secret. 없으면 None.

    User OAuth credential은 Google API 호출 시 quota project가 필수.
    우선순위: GSC_QUOTA_PROJECT env → JSON 안의 quota_project_id.
    """
    if not all(k in info for k in ("refresh_token", "client_id", "client_secret")):
        return None
    creds = UserCredentials(
        token=info.get("token") or info.get("access_token"),
        refresh_token=info["refresh_token"],
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        token_uri=info.get("token_uri", "https://oauth2.googleapis.com/token"),
        scopes=info.get("scopes") or SCOPES,
    )
    if not creds.valid:
        creds.refresh(Request())
    quota_project = os.environ.get("GSC_QUOTA_PROJECT") or info.get("quota_project_id")
    if quota_project and hasattr(creds, "with_quota_project"):
        creds = creds.with_quota_project(quota_project)
    return creds


def get_service():
    """우선순위:
      1) GSC_OAUTH_JSON  — 사용자 OAuth/ADC (refresh_token 포함)
      2) GSC_CREDS_JSON  — 서비스 계정 키
      3) 로컬 파일 fallback
    """
    oauth_json = os.environ.get("GSC_OAUTH_JSON")
    if oauth_json:
        info = json.loads(oauth_json)
        creds = _load_user_creds(info)
        if creds:
            return build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        # OAuth 형식이 아니면 서비스 계정 시도
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    creds_json = os.environ.get("GSC_CREDS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    # 로컬 파일 fallback (서비스 계정 또는 ADC)
    path = REPO_ROOT / CREDS_FILE if not Path(CREDS_FILE).is_absolute() else Path(CREDS_FILE)
    adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"

    if path.exists():
        info = json.loads(path.read_text(encoding="utf-8"))
        creds = _load_user_creds(info) or service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    if adc_path.exists():
        info = json.loads(adc_path.read_text(encoding="utf-8"))
        creds = _load_user_creds(info)
        if creds:
            return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    sys.exit(
        "[gsc_reader] 인증 실패: GSC_OAUTH_JSON · GSC_CREDS_JSON · "
        f"{path} · {adc_path} 어디에도 자격증명이 없습니다."
    )


def sa_query(service, start_date: date, end_date: date, dimensions: list[str], row_limit: int = 100):
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "dataState": "all",
    }
    return service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()


def safe_int(x) -> int:
    try:
        return int(round(float(x or 0)))
    except Exception:
        return 0


def fmt_pct(x) -> str:
    try:
        return f"{float(x or 0) * 100:.2f}%"
    except Exception:
        return "0.00%"


def fmt_pos(x) -> str:
    try:
        return f"{float(x or 0):.1f}"
    except Exception:
        return "0.0"


def short_url(u: str) -> str:
    return (
        u.replace("https://mureobom.com", "")
        .replace("https://www.mureobom.com", "")
        or "/"
    )


def main() -> int:
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=DAYS - 1)
    service = get_service()

    total_resp = sa_query(service, start_date, end_date, [])
    queries_resp = sa_query(service, start_date, end_date, ["query"], TOP_N)
    pages_resp = sa_query(service, start_date, end_date, ["page"], TOP_N)
    devices_resp = sa_query(service, start_date, end_date, ["device"])
    countries_resp = sa_query(service, start_date, end_date, ["country"], 5)

    total = (total_resp.get("rows") or [{}])[0]
    snapshot = {
        "site": SITE_URL,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": DAYS,
        },
        "total": total,
        "top_queries": queries_resp.get("rows", []),
        "top_pages": pages_resp.get("rows", []),
        "devices": devices_resp.get("rows", []),
        "countries": countries_resp.get("rows", []),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "gsc-snapshot-latest.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # observations에 붙여넣기 좋은 마크다운 요약
    lines: list[str] = []
    lines.append(f"# GSC 스냅샷 — {start_date} ~ {end_date} ({DAYS}일)")
    lines.append("")
    lines.append(f"속성: `{SITE_URL}`")
    lines.append("")
    lines.append("## 총계")
    lines.append(f"- 클릭: **{safe_int(total.get('clicks'))}**")
    lines.append(f"- 노출: **{safe_int(total.get('impressions'))}**")
    lines.append(f"- CTR: **{fmt_pct(total.get('ctr'))}**")
    lines.append(f"- 평균 게재순위: **{fmt_pos(total.get('position'))}**")
    lines.append("")

    lines.append("## 상위 검색어 (Top 10)")
    lines.append("| 검색어 | 클릭 | 노출 | CTR | 순위 |")
    lines.append("|---|---|---|---|---|")
    for r in snapshot["top_queries"][:10]:
        q = (r.get("keys") or ["?"])[0]
        lines.append(
            f"| {q} | {safe_int(r.get('clicks'))} | {safe_int(r.get('impressions'))} "
            f"| {fmt_pct(r.get('ctr'))} | {fmt_pos(r.get('position'))} |"
        )
    lines.append("")

    lines.append("## 상위 페이지 (Top 10)")
    lines.append("| 페이지 | 클릭 | 노출 | CTR | 순위 |")
    lines.append("|---|---|---|---|---|")
    for r in snapshot["top_pages"][:10]:
        p = short_url((r.get("keys") or ["?"])[0])
        lines.append(
            f"| {p} | {safe_int(r.get('clicks'))} | {safe_int(r.get('impressions'))} "
            f"| {fmt_pct(r.get('ctr'))} | {fmt_pos(r.get('position'))} |"
        )
    lines.append("")

    lines.append("## 트랙 2(재공유) 후보 — 노출 ≥10 + 클릭 0")
    candidates = [
        r for r in snapshot["top_pages"]
        if safe_int(r.get("clicks")) == 0 and safe_int(r.get("impressions")) >= 10
    ]
    if candidates:
        lines.append("| 페이지 | 노출 | 순위 |")
        lines.append("|---|---|---|")
        for r in candidates[:15]:
            p = short_url((r.get("keys") or ["?"])[0])
            lines.append(
                f"| {p} | {safe_int(r.get('impressions'))} | {fmt_pos(r.get('position'))} |"
            )
    else:
        lines.append("- 해당 없음 (모든 노출 페이지에 클릭 ≥1)")
    lines.append("")

    lines.append("## 디바이스 분포")
    if snapshot["devices"]:
        lines.append("| 디바이스 | 클릭 | 노출 | CTR |")
        lines.append("|---|---|---|---|")
        for r in snapshot["devices"]:
            d = (r.get("keys") or ["?"])[0]
            lines.append(
                f"| {d} | {safe_int(r.get('clicks'))} | {safe_int(r.get('impressions'))} "
                f"| {fmt_pct(r.get('ctr'))} |"
            )

    (OUT_DIR / "gsc-summary-latest.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(
        f"[gsc_reader] period={start_date}~{end_date} "
        f"clicks={safe_int(total.get('clicks'))} "
        f"impressions={safe_int(total.get('impressions'))} "
        f"ctr={fmt_pct(total.get('ctr'))} "
        f"position={fmt_pos(total.get('position'))}"
    )
    print(f"[gsc_reader] wrote {OUT_DIR / 'gsc-snapshot-latest.json'}")
    print(f"[gsc_reader] wrote {OUT_DIR / 'gsc-summary-latest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
