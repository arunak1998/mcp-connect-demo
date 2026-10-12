"""Connect an LLM to the MCP server: the model decides which tools to call.

    python -m mcp_demo.agent "Which region has the highest total revenue?"

Needs the `llm` extra and an API key (see .env.example).
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from mcp import ClientSession

from mcp_demo.client import connect

load_dotenv()

SYSTEM_PROMPT = """You answer questions about CSV files using the tools you are given.
1. Call get_files_list, then get_schema for the file you need.
2. Write ONE Polars SQL query and run it with execute_polars_sql.
3. In the SQL, the table is called `self`. Use WITH clauses instead of subqueries.
Answer in one or two sentences, quoting the numbers you got from the tool."""


def create_llm() -> ChatOpenAI:
    """An OpenAI-compatible chat model. LLM_BASE_URL is optional (only for a gateway)."""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-5-mini"),
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.getenv("LLM_BASE_URL") or None,
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT") or None,
        timeout=60,
    )


def tool_text(content) -> str:
    """Flatten a tool result (a string or a list of content blocks) into one short line."""
    if isinstance(content, list):
        content = " ".join(block["text"] if isinstance(block, dict) else str(block) for block in content)
    return " ".join(str(content).split())


async def ask(session: ClientSession, question: str, llm=None, on_step=print) -> str:
    """Give the server's tools to the LLM, run the loop, and return its final answer."""
    tools = await load_mcp_tools(session)  # MCP tools -> LangChain tools
    agent = create_agent(llm or create_llm(), tools=tools, system_prompt=SYSTEM_PROMPT)

    answer = ""
    async for update in agent.astream({"messages": [HumanMessage(content=question)]}, stream_mode="updates"):
        for payload in update.values():
            for message in payload.get("messages", []):
                if isinstance(message, AIMessage) and message.tool_calls:
                    for call in message.tool_calls:
                        on_step(f"LLM asks for  {call['name']}({call['args']})")
                elif isinstance(message, ToolMessage):
                    on_step(f"MCP returned  {tool_text(message.content)[:140]}")
                elif isinstance(message, AIMessage):
                    answer = message.content
    return answer


async def main() -> None:
    question = " ".join(sys.argv[1:]) or "Which region has the highest total revenue?"
    async with connect() as session:
        print(f"\nAnswer: {await ask(session, question)}")


if __name__ == "__main__":
    asyncio.run(main())
