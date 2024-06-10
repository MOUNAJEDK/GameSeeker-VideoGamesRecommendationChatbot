from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages, AnyMessage

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    query: str
    relevant: bool
    games: list[dict]
    details: dict[str, dict]
    response: str