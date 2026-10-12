"""The MCP server: three read-only tools over CSV files, served on streamable HTTP."""

import os
import sys
from glob import glob
from typing import Annotated, Any

import polars as pl
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

load_dotenv()

FILE_LOCATION = os.getenv("FILE_LOCATION", "data/*.csv")
HOST = os.getenv("MCP_HOST", "127.0.0.1")  # keep local: the SQL tool reads any path it is given
PORT = int(os.getenv("MCP_PORT", "8050"))

mcp = FastMCP("csv-tools", host=HOST, port=PORT)


@mcp.tool()
def get_files_list() -> list[str]:
    """Get the list of CSV files the server can read."""
    return glob(FILE_LOCATION)


@mcp.tool()
def get_schema(file_location: str) -> list[dict[str, str]]:
    """Return the column names and data types of a CSV file."""
    df = pl.read_csv(file_location)
    return [{"name": name, "dtype": str(dtype)} for name, dtype in df.schema.items()]


@mcp.tool()
def execute_polars_sql(
    file_locations: list[str],
    query: Annotated[
        str,
        Field(description="A Polars SQL query. Use the table name `self` to refer to the data."),
    ],
) -> list[dict[str, Any]]:
    """Run a Polars SQL query on one or more CSV files that share the same columns, and return the rows."""
    frames = [pl.scan_csv(path) for path in file_locations]
    return pl.concat(frames).collect().sql(query).to_dicts()


def main() -> None:
    # stdout carries the MCP protocol for some transports, so diagnostics go to stderr
    print(f"[server] MCP on http://{HOST}:{PORT}/mcp (files: {FILE_LOCATION})", file=sys.stderr, flush=True)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
