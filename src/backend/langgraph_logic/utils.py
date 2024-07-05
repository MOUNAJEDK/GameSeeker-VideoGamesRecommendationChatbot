from langchain_openai import ChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults 
from dotenv import load_dotenv
import os

load_dotenv()

LLM = ChatOpenAI(model="gpt-4o", temperature=0)

GOOGLE_GAME_TITLE_SEARCH = GoogleSearchAPIWrapper(
    google_cse_id=os.getenv("GOOGLE_CSE_ID_GAME_TITLE_SEARCH"),
    k=10,
)
GAME_TITLE_SEARCH_TOOL = TavilySearchResults(k=10)

GOOGLE_RAWG_IO_LINK = GoogleSearchAPIWrapper(
    google_cse_id=os.getenv("GOOGLE_CSE_ID_RAWG_IO_LINK"),
    k=1,
)
RAWG_IO_LINK_TOOL = TavilySearchResults(k=3)

GRAPH_CONFIG = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o",
    },
}