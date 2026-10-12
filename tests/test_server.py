import pytest
from tests.conftest import SAMPLE, open_session

from mcp_demo import server


def test_get_files_list_uses_file_location():
    assert server.get_files_list() == [SAMPLE]


def test_get_schema_reports_columns_and_types():
    schema = {c["name"]: c["dtype"] for c in server.get_schema(SAMPLE)}
    assert schema["region"] == "String"
    assert schema["revenue"] == "Int64"


def test_execute_polars_sql_aggregates():
    rows = server.execute_polars_sql(
        [SAMPLE], "SELECT region, SUM(revenue) AS total FROM self GROUP BY region ORDER BY total DESC"
    )
    assert [r["region"] for r in rows] == ["West", "North", "South", "East"]


def test_execute_polars_sql_rejects_a_bad_column():
    with pytest.raises(Exception, match="nope"):
        server.execute_polars_sql([SAMPLE], "SELECT nope FROM self")


async def test_server_advertises_exactly_three_tools():
    async with open_session() as session:
        listing = await session.list_tools()
    assert sorted(t.name for t in listing.tools) == ["execute_polars_sql", "get_files_list", "get_schema"]
    sql = next(t for t in listing.tools if t.name == "execute_polars_sql")
    assert sql.inputSchema["required"] == ["file_locations", "query"]
