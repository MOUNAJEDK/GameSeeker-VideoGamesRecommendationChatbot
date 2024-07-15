from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults 
from dotenv import load_dotenv
import os

load_dotenv()

LLM = ChatOpenAI(model="gpt-4o", temperature=0)

GAME_TITLE_SEARCH_TOOL = TavilySearchResults(k=10)

RAWG_IO_LINK_TOOL = TavilySearchResults(k=3)

GRAPH_CONFIG = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o",
    },
}