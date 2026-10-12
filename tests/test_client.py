import pytest
from tests.conftest import SAMPLE, open_session

from mcp_demo.client import call_text

COUNT = {"file_locations": [SAMPLE], "query": "SELECT COUNT(*) AS orders FROM self"}
BAD = {"file_locations": [SAMPLE], "query": "SELECT nope FROM self"}


async def test_call_text_returns_the_tool_output():
    async with open_session() as session:
        assert await call_text(session, "get_files_list", {}) == SAMPLE


async def test_call_text_returns_rows_as_text():
    async with open_session() as session:
        text = await call_text(session, "execute_polars_sql", COUNT)
    assert '"orders": 120' in text


async def test_a_failing_tool_raises_instead_of_returning_error_text():
    async with open_session() as session:
        with pytest.raises(RuntimeError, match="execute_polars_sql failed"):
            await call_text(session, "execute_polars_sql", BAD)


async def test_an_unknown_tool_is_an_error():
    async with open_session() as session:
        with pytest.raises(RuntimeError, match="delete_everything"):
            await call_text(session, "delete_everything", {})
