from langchain.prompts import PromptTemplate , ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent

from langgraph_logic.state import State

import json

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tool = TavilySearchResults(max_results=3)
tools = [tool]

def query_classifier(state: State):
    query_classifier_prompt = PromptTemplate(
        template=
        """
        You are part of a chatbot that provides personalized video game recommendations based on user preferences. \n
        Your task is to classify the following user query as either 'relevant' or 'irrelevant' to the topic of video game recommendations. \n\n

        A 'relevant' query includes: \n
        - Requests for game recommendations similar to a specific game (e.g., "What games are similar to Skyrim?") \n
        - Preferences for game genres (e.g., "I like open-world RPG games, can you recommend some?") \n
        - Inquiries about platform availability for games (e.g., "What games are available on PS5?") \n
        - Questions about game developers, publishers, or game details (e.g., "Who developed The Witcher 3?") \n\n

        An 'irrelevant' query includes: \n
        - General inquiries not related to video games (e.g., "What's the weather like today?") \n
        - Queries about other types of entertainment or products (e.g., "Can you recommend a good book?") \n
        - Vague questions without specific reference to video games (e.g., "Can you help me with something?") \n\n

        User Query: {query}
        """,
        input_variables=["query"],
    )

    query_classification = query_classifier_prompt | llm | StrOutputParser()
    query_classification_result = query_classification.invoke({"query": state["query"]})
    state["relevant"] = query_classification_result.lower() == "relevant"

    return state

def game_title_searcher(state: State):
    game_title_searcher_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are part of a chatbot that provides personalized video game recommendations based on user preferences. \n
                Your task is to search for video games that match the user query. \n
                Only return the titles of the games. \n
                The number of games to return is limited to 3. \n\n

                The results provided will STRICTLY look as follows (Python list): \n
                ["game_title_1", "game_title_2", "game_title_3", ...] \n
                IMPORTANT: No additional information should be included in the output. \n\n
                
                User Query: {query}
                """
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    game_title_search_agent = create_openai_tools_agent(llm, tools, game_title_searcher_prompt)
    game_title_search_agent_executor = AgentExecutor(agent=game_title_search_agent, tools=tools)
    game_title_search_agent_result = game_title_search_agent_executor.invoke({"query": state["query"], "messages": state["messages"]})
    games_list = json.loads(game_title_search_agent_result["output"].strip())

    state["messages"] = [HumanMessage(role="user", content=str(game_title_search_agent_result["output"]))]
    state["games"] = games_list

    return state

def game_details_searcher(state: State):
    game_details_searcher_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are part of a chatbot that provides personalized video game recommendations based on user preferences. \n
                Your task is to search for detailed information about each game provided. \n
                The response should be a dictionary with the game title as the key and the following information as the value: \n
                - description
                - platforms
                - genres
                - developer
                - publisher
                - release_date
                - metacritic_score \n\n

                The results provided will STRICTLY look as follows (Python dictionary): \n
                {{
                    "game_title": {{
                        "description": "description of the game",
                        "platforms": ["platform1", "platform2"],
                        "genres": ["genre1", "genre2"],
                        "developer": "developer name",
                        "publisher": "publisher name",
                        "release_date": "release date",
                        "metacritic_score": score
                    }}
                }} \n
                IMPORTANT: No additional information should be included in the output. \n\n
                
                Game Titles: {game}
                """
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    game_details_search_agent = create_openai_tools_agent(llm, tools, game_details_searcher_prompt)
    game_details_search_agent_executor = AgentExecutor(agent=game_details_search_agent, tools=tools)
    
    game_details_dict = {}
    for game in state["games"]:
        game_details_query = {"game": [game], "messages": state["messages"]}
        game_details_search_agent_result = game_details_search_agent_executor.invoke(game_details_query)
        
        output_cleaned = game_details_search_agent_result["output"].strip().strip("```python").strip("```").strip()
        game_details = json.loads(output_cleaned)
        game_details_dict.update(game_details)

    state["messages"] = [HumanMessage(role="user", content=str(game_details_search_agent_result["output"]))]
    state["details"] = game_details_dict

    return state

