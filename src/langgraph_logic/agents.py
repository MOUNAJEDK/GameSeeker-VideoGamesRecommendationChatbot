from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage
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
                The number of games to return is limited to the top 3. \n\n

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

    state["messages"] = [AIMessage(role="assistant", content=str(game_title_search_agent_result["output"]))]
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

    state["messages"] = [AIMessage(role="assistant", content=str(game_details_search_agent_result["output"]))]
    state["details"] = game_details_dict

    return state

def game_recommendation_response(state: State):
    games_details = state["details"]
    games_info = "\n\n".join(
        f"**{title}**\n"
        f"Description: {details['description']}\n"
        f"Platforms: {', '.join(details['platforms'])}\n"
        f"Genres: {', '.join(details['genres'])}\n"
        f"Developer: {details['developer']}\n"
        f"Publisher: {details['publisher']}\n"
        f"Release Date: {details['release_date']}\n"
        f"Metacritic Score: {details['metacritic_score']}"
        for title, details in games_details.items()
    )

    game_recommendation_response_prompt = PromptTemplate(
        template=
        """
        You are part of a chatbot that provides personalized video game recommendations based on user preferences. \n
        Based on the following details, generate a friendly and engaging response to the user's query.

        An example of a proper response could be: \n
        "Based on your preferences, here are some great games you might enjoy: \n
        **Game Title 1** \n
        Description: Description of the game \n
        Platforms: Platform1, Platform2 \n
        Genres: Genre1, Genre2 \n
        Developer: Developer Name \n
        Publisher: Publisher Name \n
        Release Date: Release Date \n
        Metacritic Score: Score \n\n
        ... \n\n
        We hope you find these recommendations helpful! If you have any more questions or need further assistance, feel free to ask. \n\n

        Games to Recommend: {games_info}
        """,
        input_variables=["games_info"]
    )

    game_recommendation_response = game_recommendation_response_prompt | llm | StrOutputParser()
    game_recommendation_response_result = game_recommendation_response.invoke({"games_info": games_info})

    state["messages"] = [AIMessage(role="assistant", content=game_recommendation_response_result)]

    return state