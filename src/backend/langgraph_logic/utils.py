from langchain_openai import ChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import Tool

from dotenv import load_dotenv
import os

load_dotenv()

LLM = ChatOpenAI(model="gpt-4o", temperature=0.2)

GOOGLE_GAME_TITLE_SEARCH = GoogleSearchAPIWrapper(
    google_cse_id=os.getenv("GOOGLE_CSE_ID_GAME_TITLE_SEARCH"),
    k=10,
)
GAME_TITLE_SEARCH_TOOL = Tool(
    name="game_title_search_tool",
    description="A tool that searches the web for video games that match the user query and returns the top 3 most recommended titles.",
    func=GOOGLE_GAME_TITLE_SEARCH.run,
)

GOOGLE_RAWG_IO_LINK = GoogleSearchAPIWrapper(
    google_cse_id=os.getenv("GOOGLE_CSE_ID_RAWG_IO_LINK"),
    k=1,
)
RAWG_IO_LINK_TOOL = Tool(
    name="rawg_io_link_tool",
    description="A tool that fetches the 'RAWG.io' (https://rawg.io/) web page link of a given game.",
    func=GOOGLE_RAWG_IO_LINK.run,
)

GRAPH_CONFIG = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o",
    },
}

def _print_event(event: dict, _printed: set):
    response_list = event.get("response")
    if response_list and isinstance(response_list, list):
        latest_response = response_list[-1].content
        if latest_response not in _printed:
            # print(latest_response)
            _printed.add(latest_response)
            return latest_response # Return the latest response for the API server to return
    return None