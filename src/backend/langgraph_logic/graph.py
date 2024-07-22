from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph_logic.state import State
from langgraph_logic.nodes import (
    query_classification_node, game_title_search_node, rawg_io_link_node,
    game_details_scrape_node, games_recommendation_result_node, game_extraction_node,
    answer_analysis_node, incomplete_query_handler_node, recommended_game_inquiry_node,
    sentiment_analysis_node
)
from langgraph_logic.utils import GAME_TITLE_SEARCH_TOOL, RAWG_IO_LINK_TOOL

CHECKPOINT_DB_URL = "C:/Users/karim/Desktop/GameSeeker-VideoGamesRecommendationChatbot/src/backend/db/checkpoints.db"

def create_graph(db_session_factory: Callable[[], AsyncSession]):
    checkpoint_saver = AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB_URL)
    
    game_title_search_tool_node = ToolNode(tools=[GAME_TITLE_SEARCH_TOOL])
    rawg_io_link_tool_node = ToolNode(tools=[RAWG_IO_LINK_TOOL])

    graph_builder = StateGraph(State)

    graph_builder.add_node("query_classification", query_classification_node)
    graph_builder.add_node("game_extraction", game_extraction_node)
    graph_builder.add_node("answer_analysis", answer_analysis_node(db_session_factory))
    graph_builder.add_node("game_title_search", game_title_search_node)
    graph_builder.add_node("rawg_io_link", rawg_io_link_node)
    graph_builder.add_node("game_details_scrape", game_details_scrape_node)
    graph_builder.add_node("game_title_search_tool", game_title_search_tool_node)
    graph_builder.add_node("rawg_io_link_tool", rawg_io_link_tool_node)
    graph_builder.add_node("games_recommendation_result", games_recommendation_result_node)
    graph_builder.add_node("incomplete_query_handler", incomplete_query_handler_node(db_session_factory))
    graph_builder.add_node("recommended_game_inquiry", recommended_game_inquiry_node(db_session_factory))
    graph_builder.add_node("sentiment_analysis", sentiment_analysis_node(db_session_factory))

    def query_router(state: State):
        if state["category"] == "relevant":
            return "game_extraction"
        elif state["category"] == "expressing_interest":
            if state["node_to_sentiment_analysis"] == "game_recommendation_result_node":
                return "answer_analysis"
            elif state["node_to_sentiment_analysis"] == "recommended_game_inquiry_node":
                return "sentiment_analysis"
        elif state["category"] == "incomplete":
            return "incomplete_query_handler"
        elif state["category"] == "no_most_mentioned_game":
            return END
        else:
            return END
        
    def incomplete_query_router(state: State):
        if state["category"] == "most_mentioned_game":
            return "recommended_game_inquiry"
        else:
            return END

    def should_continue_game_title_search(state: State):
        messages = state['messages']
        last_message = messages[-1]
        if "tool_calls" not in last_message.additional_kwargs:
            return "end"
        else:
            return "continue"
    
    def should_continue_rawg_io_link(state: State):
        messages = state['messages']
        last_message = messages[-1]
        if "tool_calls" in last_message.additional_kwargs:
            return "continue"
        else:
            if state["index"] < len(state["games"]):
                return "increment"
            else:
                return "end"
            
    def answer_analysis_router(state: State):
        if state["for_user"]:
            return "sentiment_analysis"
        else:
            return END
        
    def sentiment_analysis_router(state: State):
        if state["node_to_sentiment_analysis"] == "recommended_game_inquiry_node":
            return "game_title_search"
        else:
            return END
        
    def recommended_game_inquiry_router(state: State):
<<<<<<< HEAD
        if state["inquiry_next_node"] == "game_title_search":
            return "game_title_search"
        else:
            return END
=======
        if state["inquiry_next_node"] == "sentiment_analysis_node":
            return END
        else:
            return "game_title_search"
>>>>>>> 1d1924342736f0feea7e59bb47a3abbc02f5e796

    graph_builder.add_conditional_edges("query_classification", query_router)
    graph_builder.add_conditional_edges("incomplete_query_handler", incomplete_query_router)
    graph_builder.add_conditional_edges(
        "game_title_search",
        should_continue_game_title_search,
        {"continue": "game_title_search_tool", "end": "rawg_io_link"},
    )
    graph_builder.add_conditional_edges(
        "rawg_io_link",
        should_continue_rawg_io_link,
        {"continue": "rawg_io_link_tool", "increment": "rawg_io_link", "end": "game_details_scrape"},
    )

    graph_builder.add_edge("game_extraction", "game_title_search")
    graph_builder.add_conditional_edges("answer_analysis", answer_analysis_router)
    graph_builder.add_edge("game_title_search_tool", "game_title_search")
    graph_builder.add_edge("rawg_io_link_tool", "rawg_io_link")
    graph_builder.add_edge("game_details_scrape", "games_recommendation_result")
    graph_builder.add_conditional_edges("sentiment_analysis", sentiment_analysis_router)
    graph_builder.add_conditional_edges("recommended_game_inquiry", recommended_game_inquiry_router)

    graph_builder.set_entry_point("query_classification")
    graph_builder.set_finish_point("games_recommendation_result")

    return graph_builder.compile(checkpointer=checkpoint_saver)