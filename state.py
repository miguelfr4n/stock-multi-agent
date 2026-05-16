from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class InventoryState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next: str
    iterations: int
    agents_used: list[str]
