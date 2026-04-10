"""Tests for flight_dynamic_sql date bounds and SQL template."""

from datetime import date

import pytest

from xagent.core.tools.core.flight_dynamic_sql import (
    MAX_RANGE_DAYS,
    _build_daily_stats_sql,
    _resolve_range,
)


def test_resolve_range_default_end_is_used() -> None:
    start_d, end_d = _resolve_range(None, "2025-06-15")
    assert end_d.isoformat() == "2025-06-15"
    span = (end_d - start_d).days + 1
    assert span == 90


def test_resolve_range_explicit() -> None:
    start_d, end_d = _resolve_range("2025-01-01", "2025-01-07")
    assert start_d.isoformat() == "2025-01-01"
    assert end_d.isoformat() == "2025-01-07"


def test_resolve_range_start_after_end_raises() -> None:
    with pytest.raises(ValueError, match="must be on or before"):
        _resolve_range("2025-02-01", "2025-01-01")


def test_resolve_range_too_long_raises() -> None:
    with pytest.raises(ValueError, match="maximum allowed"):
        _resolve_range("2024-01-01", "2025-12-31")


def test_build_sql_contains_bounds_and_table() -> None:
    sql = _build_daily_stats_sql(date(2025, 1, 1), date(2025, 1, 3))
    assert "t_flight_dynamic_report" in sql
    assert "2025-01-01 00:00:00" in sql
    assert "2025-01-04 00:00:00" in sql
    assert "TO_DATE(create_time)" in sql


def test_max_range_constant() -> None:
    assert MAX_RANGE_DAYS == 366
