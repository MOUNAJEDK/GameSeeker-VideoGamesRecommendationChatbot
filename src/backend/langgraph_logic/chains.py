from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph_logic.utils import LLM, GAME_TITLE_SEARCH_TOOL, RAWG_IO_LINK_TOOL

query_classification_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations. Your task is to classify the following user query into one of the following categories:
            
            1. 'relevant' - Queries seeking video game recommendations.
                - Example: "What games are similar to Skyrim?"
                - Example: "I like open-world RPG games, can you recommend some?"
                - Example: "What games do you recommend for PS5?"
                - Example: "Can you recommend games developed by Square Enix?"

            2. 'irrelevant' - Queries unrelated to video games.
                - Example: "What's the weather like today?"
                - Example: "Can you recommend a good book?"

            3. 'greeting' - General greetings or questions about the chatbot.
                - Example: "Hi!"
                - Example: "Who are you?"
                - Example: "What's your objective?"

            4. 'incomplete' - Queries that are too vague or ambiguous.
                - Example: "I want to play something."
                - Example: "Give me some suggestions."
                - Example: "What should I play?"
                - Example: "Recommend me something."

            5. 'expressing_interest' - Responses expressing interest or experience with a game.
                - Example: "Yes, I love Minecraft!"
                - Example: "I've been playing it for years."
                - Example: "My friend can't stop talking about it."

            Your response should be the name of the category (no quotation marks to be displayed in the output): 'relevant', 'irrelevant', 'greeting', 'incomplete', or 'expressing_interest'. Nothing more, nothing less.
            """
        ),
        ("user", "User Query: {query}"),
        ("placeholder", "{messages}"),
    ]
)

query_classification = query_classification_prompt | LLM | StrOutputParser()

game_title_search_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations. 
            Your task is to search the web for video games that match the user query and return the top 3 most recommended titles.
            
            Criteria for filtering the games include:
            1. Number of mentions or most praises
            2. Highest scores (if available)

            Your response should be a Python list containing the titles of the games (as strings) in the following format:
            ["game_title_1", "game_title_2", "game_title_3"]
            Do not include any additional information in the output.
            """
        ),
        ("user", "User Query: {query}"),
        ("placeholder", "{messages}"),
    ]
)

game_title_search = game_title_search_prompt | LLM.bind_tools([GAME_TITLE_SEARCH_TOOL])

rawg_io_link_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations. 
            Your task is to search the web for the game's RAWG.io web page and provide the direct link to it.
            
            The response should be the direct link to the game's RAWG.io web page. No additional information should be included.
            Example: https://rawg.io/games/the-witcher-3-wild-hunt
            """
        ),
        ("user", "You are to fetch the link for the game: {game}"),
        ("placeholder", "{messages}"),
    ]
)

rawg_io_link = rawg_io_link_prompt | LLM.bind_tools([RAWG_IO_LINK_TOOL])

game_extraction_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations.
            Your task is to extract the name of the video game mentioned in the user's query.
            
            Your response should be only the name of the game, nothing more.
            Example: "I'm looking for games similar to Skyrim." -> "Skyrim"
            """
        ),
        ("user", "User Query: {query}"),
    ]
)

game_extraction = game_extraction_prompt | LLM | StrOutputParser()

answer_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations.
            Your task is to determine if the user's response indicates that they have personal experience with the game or if they're asking about it for someone else.
            
            Respond with:
            - "for_user" if the response indicates personal experience or interest.
            - "for_others" if the response suggests they're asking for someone else or have no personal experience.
            
            Your response should be only one of these two options, nothing more.
            Example: "Yes, I love Minecraft!" -> "for_user"
            Example: "My friend can't stop talking about it." -> "for_others"
            """
        ),
        ("user", "User Response: {response}"),
    ]
)

answer_analysis = answer_analysis_prompt | LLM | StrOutputParser()