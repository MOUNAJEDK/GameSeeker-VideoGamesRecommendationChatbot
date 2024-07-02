from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages, AnyMessage
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    query: str
    category: str
    games: list[str]
    details: dict[str, dict]
    links: list[str]
    index: int
    response: str
    user_id: int
    extracted_game: str