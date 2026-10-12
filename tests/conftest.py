from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_demo import server

SAMPLE = str(Path(__file__).parents[1] / "data" / "sample_sales.csv")


@pytest.fixture(autouse=True)
def sample_data(monkeypatch):
    monkeypatch.setattr(server, "FILE_LOCATION", SAMPLE)


@asynccontextmanager
async def open_session():
    """A real MCP client session wired to the server in memory (no network)."""
    async with create_connected_server_and_client_session(server.mcp._mcp_server) as client:
        yield client
