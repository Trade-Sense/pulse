from functools import lru_cache
from typing import List, Optional

from llama_index.core.llms import LLM, ChatMessage
from llama_index.core.tools import ToolSelection
from llama_index.core.workflow import Event, Workflow, step
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel


class TextExtraction(BaseModel):
    """Extract basic information"""

    texts: List[str]


class SentimentDetails(BaseModel):
    """Generate sentiment details from input"""

    sentiment_score: float
    sentiment_label: str


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class RouterInputEvent(Event):
    input: list[ChatMessage]


class SentimentAgent(Workflow):
    def __init__(self, llm: LLM, timeout: Optional[float] = 300):
        super().__init__(timeout=timeout)
        self.llm = llm

    @step
    async def tool_call_handler(self, ev: ToolCallEvent) -> RouterInputEvent:
        tool_calls = ev.tool_calls

        for tool_call in tool_calls:
            function_name = tool_call.tool_name
            arguments = tool_call.tool_kwargs
            if "input" in arguments:
                arguments["prompt"] = arguments.pop("input")

            try:
                function_callable = skill_map.get_function_callable_by_name(function_name)
            except KeyError:
                function_result = "Error: Unknown function call"

            function_result = function_callable(arguments)
            message = ChatMessage(
                role="tool",
                content=function_result,
                additional_kwargs={"tool_call_id": tool_call.tool_id},
            )

            self.memory.put(message)

        return RouterInputEvent(input=self.memory.get())


@lru_cache(maxsize=1)
def get_agent() -> SentimentAgent:
    llm = Ollama(model="llama3.2", tools=tools)
    agent = SentimentAgent(llm=llm)
    return agent


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Get the current sentiment to the given symbol from the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]
