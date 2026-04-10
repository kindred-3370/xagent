"""
Flight dynamic report: fixed daily row-count aggregation for Doris (MySQL protocol).

Uses the same connection resolution as sql_tool (XAGENT_EXTERNAL_DB_FLIGHT_DORIS).
SQL is template-only; only validated date bounds are interpolated.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

from .sql_tool import execute_sql_query

if TYPE_CHECKING:
    from ...workspace import TaskWorkspace

logger = logging.getLogger(__name__)

# Must match env XAGENT_EXTERNAL_DB_FLIGHT_DORIS and Agent instructions.
FLIGHT_DORIS_CONNECTION_NAME = "FLIGHT_DORIS"
FLIGHT_DYNAMIC_TABLE = "t_flight_dynamic_report"
DEFAULT_RANGE_DAYS = 90
MAX_RANGE_DAYS = 366
# Web UI reads tool trace results with this schema_version (do not rename lightly).
FLIGHT_DAILY_STATS_SCHEMA_V1 = "flight_daily_stats_v1"

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_iso_date(value: str) -> date:
    s = value.strip()
    if not _ISO_DATE.match(s):
        raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {value!r}")
    y, m, d = (int(s[0:4]), int(s[5:7]), int(s[8:10]))
    return date(y, m, d)


def _resolve_range(
    start_date: Optional[str], end_date: Optional[str]
) -> tuple[date, date]:
    """Return inclusive (start_d, end_d) in UTC calendar dates."""
    today = datetime.now(timezone.utc).date()
    if end_date and end_date.strip():
        end_d = _parse_iso_date(end_date)
    else:
        end_d = today
    if start_date and start_date.strip():
        start_d = _parse_iso_date(start_date)
    else:
        start_d = end_d - timedelta(days=DEFAULT_RANGE_DAYS - 1)
    if start_d > end_d:
        raise ValueError(f"start_date {start_d} must be on or before end_date {end_d}")
    span = (end_d - start_d).days + 1
    if span > MAX_RANGE_DAYS:
        raise ValueError(
            f"Date range spans {span} days; maximum allowed is {MAX_RANGE_DAYS} days"
        )
    return start_d, end_d


def _build_daily_stats_sql(start_d: date, end_d: date) -> str:
    """Build Doris SQL with bound time range on create_time (half-open interval)."""
    start_lit = f"{start_d.isoformat()} 00:00:00"
    end_exclusive = end_d + timedelta(days=1)
    end_lit = f"{end_exclusive.isoformat()} 00:00:00"
    table = FLIGHT_DYNAMIC_TABLE
    return f"""
SELECT
    dt AS stat_date,
    COUNT(*) AS row_count
FROM (
    SELECT TO_DATE(create_time) AS dt
    FROM {table}
    WHERE create_time >= '{start_lit}' AND create_time < '{end_lit}'
) temp
GROUP BY dt
ORDER BY dt ASC
""".strip()


def fetch_flight_dynamic_daily_stats(
    *,
    connection_name: str = FLIGHT_DORIS_CONNECTION_NAME,
    connection_url: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    workspace: Optional["TaskWorkspace"] = None,
) -> dict[str, Any]:
    """Run fixed daily aggregation; returns LLM-friendly dict."""
    try:
        start_d, end_d = _resolve_range(start_date, end_date)
    except ValueError as e:
        return {
            "schema_version": FLIGHT_DAILY_STATS_SCHEMA_V1,
            "success": False,
            "error": str(e),
            "range": None,
            "series": [],
            "row_count": 0,
            "message": f"Invalid parameters: {e}",
        }

    query = _build_daily_stats_sql(start_d, end_d)
    try:
        raw = execute_sql_query(
            connection_name,
            query,
            output_file=None,
            workspace=workspace,
            connection_url=connection_url,
        )
    except ValueError as e:
        err = str(e)
        logger.warning("Flight dynamic stats: connection error: %s", e)
        if "not found" in err.lower() and "connection" in err.lower():
            hint = (
                f"{err} Set environment variable "
                "XAGENT_EXTERNAL_DB_FLIGHT_DORIS=mysql+pymysql://root:@HOST:9030/xagent "
                "(no password: keep the colon before @) or USER:PASS@HOST:9030/xagent "
                "(database xagent, Doris FE port typically 9030), then restart the server."
            )
        else:
            hint = err
        return {
            "schema_version": FLIGHT_DAILY_STATS_SCHEMA_V1,
            "success": False,
            "error": hint,
            "range": {
                "start": start_d.isoformat(),
                "end": end_d.isoformat(),
            },
            "series": [],
            "row_count": 0,
            "message": hint,
        }
    except Exception as e:
        logger.exception("Flight dynamic stats query failed")
        return {
            "schema_version": FLIGHT_DAILY_STATS_SCHEMA_V1,
            "success": False,
            "error": str(e),
            "range": {
                "start": start_d.isoformat(),
                "end": end_d.isoformat(),
            },
            "series": [],
            "row_count": 0,
            "message": f"Query failed: {e}",
        }

    if not raw.get("success"):
        return {
            "schema_version": FLIGHT_DAILY_STATS_SCHEMA_V1,
            "success": False,
            "error": raw.get("message", "unknown error"),
            "range": {
                "start": start_d.isoformat(),
                "end": end_d.isoformat(),
            },
            "series": [],
            "row_count": 0,
            "message": raw.get("message", ""),
        }

    series: list[dict[str, Any]] = []
    for row in raw.get("rows") or []:
        if not isinstance(row, dict):
            continue
        stat_date = row.get("stat_date")
        cnt = row.get("row_count")
        if stat_date is None:
            continue
        if hasattr(stat_date, "isoformat"):
            stat_date = stat_date.isoformat()
        else:
            stat_date = str(stat_date)
        try:
            count_int = int(cnt) if cnt is not None else 0
        except (TypeError, ValueError):
            count_int = 0
        series.append({"date": stat_date, "count": count_int})

    return {
        "schema_version": FLIGHT_DAILY_STATS_SCHEMA_V1,
        "success": True,
        "error": None,
        "range": {
            "start": start_d.isoformat(),
            "end": end_d.isoformat(),
        },
        "series": series,
        "row_count": len(series),
        "message": (
            f"Daily row counts for {FLIGHT_DYNAMIC_TABLE} "
            f"from {start_d.isoformat()} to {end_d.isoformat()} "
            f"({len(series)} day(s) with data). "
            f"Connection: {connection_name}."
        ),
    }
