from langchain_core.messages import AIMessage
from scrapegraphai.graphs import SmartScraperGraph
from scrapegraphai.utils import prettify_exec_info

from langgraph_logic.utils import GRAPH_CONFIG
from langgraph_logic.chains import query_classification, game_title_search, rawg_io_link
from langgraph_logic.state import State

import json

def query_classification_node(state: State):
    query_classification_output = query_classification.invoke({"query": state["query"], "messages": state["messages"]})

    if query_classification_output.lower().strip() == "relevant":
        state["category"] = "relevant"
        state["messages"] = [query_classification_output]
        state["response"] = [AIMessage(content="🔍 I'm now searching for video game recommendations based on your query...\n\n")]
        return state
    elif query_classification_output.lower().strip() == "irrelevant":
        state["category"] = "irrelevant"
        state["messages"] = [query_classification_output]
        state["response"] = [AIMessage(content="❗ I'm sorry, but I'm only able to provide video game recommendations. Please ask me a question related to video games.")]
        return state
    elif query_classification_output.lower().strip() == "greeting":
        state["category"] = "greeting"
        state["messages"] = [query_classification_output]
        state["response"] = [AIMessage(content="👋 Hello! I'm an AI assistant specialized in providing personalized video game recommendations. 🎮 Feel free to ask me anything related to video games.")]
        return state
    elif query_classification_output.lower().strip() == "incomplete":
        state["category"] = "incomplete"
        state["messages"] = [query_classification_output]
        state["response"] = [AIMessage(content="📝 I'm sorry, but I need more information to provide you with video game recommendations. Please be more specific in your query.")]
        return state

def game_title_search_node(state: State):
    game_title_search_output = game_title_search.invoke({"query": state["query"], "messages": state["messages"]})
    state["messages"] = [game_title_search_output]

    if state["messages"][-1].content:
        state["games"] = json.loads(state["messages"][-1].content)

        games_list = state["games"]
        games_message = "🎮 **Top Recommended Games for You:** 🎮\n"
        for game in games_list:
            games_message += f"    • 🕹️ **{game}**\n"

        message = AIMessage(content=games_message)
        state["response"] = [message]

    return state

def rawg_io_link_node(state: State):
    game = state["games"][state["index"]]
    rawg_io_link_output = rawg_io_link.invoke({"game": game, "messages": state["messages"]})
    
    state["messages"] = [rawg_io_link_output]

    if state["messages"][-1].content:
        link = state["messages"][-1].content
        state["links"].append(link)
        state["index"] += 1

    return state

def game_details_scrape_node(state: State):
    message = "\n\n➕ **Here is some additional info on each game:** ➕\n"

    for index, link in enumerate(state["links"]):
        smart_scraper_graph = SmartScraperGraph(
            prompt="Extract the following information from the source: 'About', 'Genre', 'Platforms', 'Release date', 'Developer' and 'Publisher'.",
            source=link,
            config=GRAPH_CONFIG,
        )

        game_details = smart_scraper_graph.run()

        game_name = state["games"][index]
        state["details"][game_name] = game_details

        message += f"• 🎮 **{game_name}**\n"
        message += f"    - 📖 **About**: {game_details.get('About', 'N/A')}\n"
        message += f"    - 🎨 **Genre**: {game_details.get('Genre', 'N/A')}\n"
        message += f"    - 🖥️ **Platforms**: {game_details.get('Platforms', 'N/A')}\n"
        message += f"    - 📅 **Release date**: {game_details.get('Release date', 'N/A')}\n"
        message += f"    - 🛠️ **Developer**: {game_details.get('Developer', 'N/A')}\n"
        message += f"    - 🏢 **Publisher**: {game_details.get('Publisher', 'N/A')}\n"

    state["response"] = [AIMessage(content=message)]
    
    return state