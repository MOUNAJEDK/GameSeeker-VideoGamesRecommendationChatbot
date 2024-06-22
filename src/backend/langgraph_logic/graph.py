from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from langgraph_logic.state import State
from langgraph_logic.nodes import query_classification_node, game_title_search_node, rawg_io_link_node, game_details_scrape_node
from langgraph_logic.utils import GAME_TITLE_SEARCH_TOOL, RAWG_IO_LINK_TOOL

game_title_search_tool_node = ToolNode(tools=[GAME_TITLE_SEARCH_TOOL])
rawg_io_link_tool_node = ToolNode(tools=[RAWG_IO_LINK_TOOL])

graph_builder = StateGraph(State)

graph_builder.add_node("query_classification", query_classification_node)
graph_builder.add_node("game_title_search", game_title_search_node)
graph_builder.add_node("rawg_io_link", rawg_io_link_node)
graph_builder.add_node("game_details_scrape", game_details_scrape_node)
graph_builder.add_node("game_title_search_tool", game_title_search_tool_node)
graph_builder.add_node("rawg_io_link_tool", rawg_io_link_tool_node)

def query_router(state: State):
    if state["category"] == "relevant":
        return "game_title_search"
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

graph_builder.add_conditional_edges("query_classification", query_router)
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

graph_builder.add_edge("game_title_search_tool", "game_title_search")
graph_builder.add_edge("rawg_io_link_tool", "rawg_io_link")

graph_builder.set_entry_point("query_classification")
graph_builder.set_finish_point("game_details_scrape")

graph = graph_builder.compile()