from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from scrapegraphai.graphs import SmartScraperGraph

from langgraph_logic.utils import GRAPH_CONFIG
from langgraph_logic.chains import query_classification, game_title_search, rawg_io_link, game_extraction, answer_analysis
from langgraph_logic.state import State

import json
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)

from models import MentionedGame

def query_classification_node(state: State):
    query_classification_output = query_classification.invoke({"query": state["query"], "messages": state["messages"]})

    if query_classification_output.lower().strip() == "relevant":
        state["category"] = "relevant"
        state["messages"] = [query_classification_output]
    elif query_classification_output.lower().strip() == "irrelevant":
        state["category"] = "irrelevant"
        state["messages"] = [query_classification_output]
        state["response"] = "❗ I'm sorry, but I'm only able to provide video game recommendations. Please ask me a question related to video games."
    elif query_classification_output.lower().strip() == "greeting":
        state["category"] = "greeting"
        state["messages"] = [query_classification_output]
        state["response"] = "👋 Hello! I'm an AI assistant specialized in providing personalized video game recommendations. 🎮 Feel free to ask me anything related to video games."
    elif query_classification_output.lower().strip() == "incomplete":
        state["category"] = "incomplete"
        state["messages"] = [query_classification_output]
    elif query_classification_output.lower().strip() == "expressing_interest":
        state["category"] = "expressing_interest"
        state["messages"] = [query_classification_output]
        
    return state

def game_extraction_node(state: State):
    extracted_game = game_extraction.invoke({"query": state["query"]})
    state["extracted_game"] = extracted_game.title()
    return state

def game_title_search_node(state: State):
    game_title_search_output = game_title_search.invoke({"query": state["query"], "messages": state["messages"]})
    state["messages"] = [game_title_search_output]

    if state["messages"][-1].content:
        state["games"] = json.loads(state["messages"][-1].content)

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
    for index, link in enumerate(state["links"]):
        smart_scraper_graph = SmartScraperGraph(
            prompt="Extract the following information from the source: 'About', 'Genre', 'Platforms', 'Release date', 'Developer' and 'Publisher'.",
            source=link,
            config=GRAPH_CONFIG,
        )

        game_details = smart_scraper_graph.run()

        game_name = state["games"][index]
        state["details"][game_name] = game_details
    
    return state

def games_recommendation_result_node(state: State):
    message = "🔎Upon analyzing your query, I've come up with the following game recommendations for you:🔎\n\n"

    message += "🎮 **Top Recommended Games for You:** 🎮\n"
    for game in state["games"]:
        message += f"    • 🕹️ **{game}**\n"

    message += "\n\n➕ **Here is some additional info on each game:** ➕\n"
    for game_name, game_details in state["details"].items():
        message += f"• 🎮 **{game_name}**\n"
        message += f"    - 📖 **About**: {game_details.get('About', 'N/A')}\n"
        message += f"    - 🎨 **Genre**: {game_details.get('Genre', 'N/A')}\n"
        message += f"    - 🖥️ **Platforms**: {game_details.get('Platforms', 'N/A')}\n"
        message += f"    - 📅 **Release date**: {game_details.get('Release date', 'N/A')}\n"
        message += f"    - 🛠️ **Developer**: {game_details.get('Developer', 'N/A')}\n"
        message += f"    - 🏢 **Publisher**: {game_details.get('Publisher', 'N/A')}\n"

    if state["category"] == "relevant":
        message += f"\n\nIf you don't mind me asking, have you played or are you still playing {state['extracted_game']}? And if so, how did you like it? Was it enjoyable?"

    state["response"] = message
    return state

def answer_analysis_node(db_session_factory: Callable[[], AsyncSession]):
    async def _answer_analysis_node(state: State):
        analysis_result = answer_analysis.invoke({"response": state["query"]})
        state["for_user"] = analysis_result == "for_user"
        state["response"] = "Oh, that's lovely to hear! Glad you're enjoying it!" if state["for_user"] else "Oh, that's lovely to hear! Glad they're enjoying it!"
        
        if state["for_user"]:
            async with db_session_factory() as db:
                # Check if the game is already mentioned for this user
                result = await db.execute(
                    select(MentionedGame).where(
                        (MentionedGame.user_id == state["user_id"]) & 
                        (MentionedGame.game_title == state["extracted_game"])
                    )
                )
                existing_game = result.scalar_one_or_none()
                
                if not existing_game:
                    new_mentioned_game = MentionedGame(
                        user_id=state["user_id"],
                        game_title=state["extracted_game"]
                    )
                    db.add(new_mentioned_game)
                    state["response"] += f"\nI've noted your interest in {state['extracted_game']}."
                else:
                    existing_game.mention_count += 1
                    state["response"] += f"\nI see you've mentioned {state['extracted_game']} again."
                
                await db.commit()
        else:
            state["response"] += f"\nI understand that you're asking about {state['extracted_game']} for someone else."
        
        return state

    return _answer_analysis_node

def incomplete_query_handler(db_session_factory: Callable[[], AsyncSession]):
    async def _incomplete_query_handler(state: State):
        async with db_session_factory() as db:
            result = await db.execute(
                select(MentionedGame)
                .where(MentionedGame.user_id == state["user_id"])
                .order_by(MentionedGame.mention_count.desc())
                .limit(1)
            )
            most_mentioned_game = result.scalar_one_or_none()

            if most_mentioned_game:
                state["query"] = f"I want games similar to {most_mentioned_game.game_title}"
                state["category"] = "most_mentioned_game"
            else:
                state["response"] = "I'm sorry, but your query is ambiguous, and I don't have any previous game mentions from you to work with. Could you please provide more specific information about the kind of game you're looking for?"
                state["category"] = "no_most_mentioned_game"

        return state

    return _incomplete_query_handler