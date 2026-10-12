"""A plain MCP client: connect, list the tools, call one. No LLM involved.

python -m mcp_demo.client
"""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from mcp_demo import DEFAULT_URL

SQL = "SELECT region, SUM(revenue) AS total FROM self GROUP BY region ORDER BY total DESC"


@asynccontextmanager
async def connect(url: str | None = None) -> AsyncIterator[ClientSession]:
    """Open an MCP session (this performs the `initialize` handshake)."""
    url = url or os.getenv("MCP_SERVER_URL", DEFAULT_URL)
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_text(session: ClientSession, name: str, arguments: dict[str, Any]) -> str:
    """Call a tool and return its text content. Raises if the tool reports an error."""
    result = await session.call_tool(name, arguments)
    text = "\n".join(block.text for block in result.content if block.type == "text")
    if result.isError:
        raise RuntimeError(f"Tool {name} failed: {text}")
    return text


async def main() -> None:
    async with connect() as session:
        listing = await session.list_tools()
        print("Tools offered by the server:")
        for tool in listing.tools:
            print(f"  - {tool.name}({', '.join(tool.inputSchema.get('properties', {}))})")

        files = await call_text(session, "get_files_list", {})
        print(f"\nget_files_list -> {files}")
        path = files.splitlines()[0]
        print("\nexecute_polars_sql ->")
        print(
            await call_text(
                session,
                "execute_polars_sql",
                {
                    "file_locations": [path],
                    "query": SQL,
                },
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
