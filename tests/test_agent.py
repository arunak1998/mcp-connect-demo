from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from tests.conftest import SAMPLE, open_session

from mcp_demo.agent import ask, tool_text


class ScriptedModel(GenericFakeChatModel):
    """Plays back fixed AI messages and accepts tool bindings like a real chat model."""

    def bind_tools(self, tools, **kwargs):
        return self


async def test_the_llm_uses_an_mcp_tool_then_answers():
    sql_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "execute_polars_sql",
                "args": {"file_locations": [SAMPLE], "query": "SELECT COUNT(*) AS orders FROM self"},
                "id": "call_1",
            }
        ],
    )
    llm = ScriptedModel(messages=iter([sql_call, AIMessage(content="There are 120 orders.")]))
    steps: list[str] = []

    async with open_session() as session:
        answer = await ask(session, "How many orders?", llm=llm, on_step=steps.append)

    assert answer == "There are 120 orders."
    assert steps[0].startswith("LLM asks for  execute_polars_sql")
    assert '"orders": 120' in steps[1]


def test_tool_text_flattens_content_blocks():
    blocks = [{"type": "text", "text": '{\n  "region": "West"\n}'}, {"type": "text", "text": "next"}]
    assert tool_text(blocks) == '{ "region": "West" } next'
