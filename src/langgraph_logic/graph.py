from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from langgraph_logic.state import State
from langgraph_logic.agents import query_classifier, query_not_relevant, game_title_searcher, game_details_searcher, game_recommendation_response

def query_router(state: State):
    if state["relevant"]:
        return "game_title_search"
    else:
        return "query_not_relevant"

graph_builder = StateGraph(State)
graph_builder.add_node("query_classifier", query_classifier)
graph_builder.add_node("query_not_relevant", query_not_relevant)
graph_builder.add_node("game_title_search", game_title_searcher)
graph_builder.add_node("game_details_search", game_details_searcher)
graph_builder.add_node("game_recommendation_response", game_recommendation_response)

graph_builder.add_edge("game_title_search", "game_details_search")
graph_builder.add_edge("game_details_search", "game_recommendation_response")
graph_builder.add_edge("query_not_relevant", END)

graph_builder.add_conditional_edges("query_classifier", query_router)

graph_builder.set_entry_point("query_classifier")
graph_builder.set_finish_point("game_recommendation_response")
graph = graph_builder.compile()