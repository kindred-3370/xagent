"""
Flight dynamic daily stats tool — DATABASE category, fixed SQL via flight_dynamic_sql.

Enable only on dedicated agents via allowed_tools: get_flight_dynamic_daily_stats
"""

import logging
from textwrap import dedent, indent
from typing import TYPE_CHECKING, Any, Optional

from ....workspace import TaskWorkspace
from ...core.flight_dynamic_sql import (
    FLIGHT_DORIS_CONNECTION_NAME,
    fetch_flight_dynamic_daily_stats,
)
from .base import ToolCategory
from .factory import ToolFactory, register_tool
from .function import FunctionTool

if TYPE_CHECKING:
    from .config import BaseToolConfig

logger = logging.getLogger(__name__)


class FlightDynamicFunctionTool(FunctionTool):
    """Flight dynamic stats tool — DATABASE category."""

    category = ToolCategory.DATABASE


class FlightDynamicTool:
    """Bound workspace + connection map for flight dynamic stats."""

    def __init__(
        self,
        workspace: Optional[TaskWorkspace] = None,
        connection_map: Optional[dict[str, str]] = None,
    ):
        self._workspace = workspace
        self._connection_map = {
            key.upper(): value for key, value in (connection_map or {}).items()
        }

    def _resolve_connection_url(self, connection_name: str) -> Optional[str]:
        return self._connection_map.get(connection_name.upper())

    def get_flight_dynamic_daily_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        return fetch_flight_dynamic_daily_stats(
            connection_name=FLIGHT_DORIS_CONNECTION_NAME,
            connection_url=self._resolve_connection_url(FLIGHT_DORIS_CONNECTION_NAME),
            start_date=start_date,
            end_date=end_date,
            workspace=self._workspace,
        )

    def get_tools(self) -> list[FlightDynamicFunctionTool]:
        return [
            FlightDynamicFunctionTool(
                self.get_flight_dynamic_daily_stats,
                name="get_flight_dynamic_daily_stats",
                description=indent(
                    dedent("""
                    Query flight dynamic report daily row counts from Doris.

                    Uses fixed aggregation on table t_flight_dynamic_report (TO_DATE(create_time)).
                    Connection name is always FLIGHT_DORIS (configure XAGENT_EXTERNAL_DB_FLIGHT_DORIS).

                    For natural-language questions about "daily flight dynamics statistics", call this
                    tool first; summarize results for the user and state the actual date range used.

                    Args:
                        start_date: Optional start date inclusive, format YYYY-MM-DD.
                            If omitted, defaults to (end_date - 89 days) or last 90 days through end_date.
                        end_date: Optional end date inclusive, format YYYY-MM-DD.
                            If omitted, defaults to today (UTC).

                    Returns:
                        dict with:
                        - success: bool
                        - range: { start, end } ISO dates actually queried
                        - series: [ { date, count }, ... ] sorted by date ascending
                        - row_count: number of days with data in the series
                        - message: short summary
                        - error: message if success is false

                    Constraints:
                        - Maximum span is 366 days.
                    """),
                    "",
                ),
                tags=["sql", "database", "doris", "flight", "statistics"],
            ),
        ]


@register_tool
async def create_flight_dynamic_tools(config: "BaseToolConfig") -> list:
    workspace = ToolFactory._create_workspace(config.get_workspace_config())
    connection_map = config.get_sql_connections()
    return FlightDynamicTool(workspace, connection_map).get_tools()
