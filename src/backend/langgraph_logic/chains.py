from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph_logic.utils import LLM, GAME_TITLE_SEARCH_TOOL, RAWG_IO_LINK_TOOL

query_classification_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations. Your task is to classify the following user query into one of the following categories:
            
            1. 'relevant' - Queries seeking video game recommendations, strictly asking for similar games to a mentioned title.
                - Example: "What games are similar to Skyrim?"
                - Example: "Can you recommend games like Minecraft?"
                - Example: "I love playing Stardew Valley. What other games are similar?"
                - Example: "I'm looking for games similar to The Witcher 3."

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

            5. 'expressing_interest' - Responses expressing interest/lack of interest in a video game or mentioning the overall sentiment towards it.
                - Example: "Yes, I love Minecraft!"
                - Example: "I've been playing it for years."
                - Example: "My friend can't stop talking about it."
                - Example: "I don't like it that much."
                - Example: "I've never played it before."

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
            Example: ["The Witcher 3: Wild Hunt", "Red Dead Redemption 2", "Dark Souls III"]
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
        ("placeholder", "{messages}")
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
            - "for_user" if the response indicates personal experience, interest, positiv/negative/netural opinion or overall a sentiment towards the game that suggests they're asking for themselves.
            - "for_others" if the response suggests they're asking for someone else, have no personal experience with the game, or overall the expressed opinion doesn't reflect their own.
            
            Your response should be only one of these two options, nothing more.
            Example: "Yes, I love Minecraft!" -> "for_user"
            Example: "My friend can't stop talking about it." -> "for_others"
            Example: "It's OK, but not my favorite." -> "for_user"
            Example: "I've never played it before." -> "for_others"
            Example: "I didn't enjoy it as much as I thought I would." -> "for_user"
            """
        ),
        ("user", "User Response: {response}"),
        ("placeholder", "{messages}")
    ]
)

answer_analysis = answer_analysis_prompt | LLM | StrOutputParser()

sentiment_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI assistant specialized in providing personalized video game recommendations.
            Your task is to analyze the sentiment of the given user query and provide a score between -1 and +1, not including the boundaries.
            
            Guidelines:
            - A score of ~-1 represents extremely negative sentiment
            - A score of 0 represents neutral sentiment
            - A score of ~+1 represents extremely positive sentiment
            - You can use any value between -1 and +1 for nuanced sentiment
            
            Provide only the numerical score as your response, nothing else.
            Example: "I love playing Stardew Valley." -> +0.8
            Example: "I'm not a fan of Call of Duty." -> -0.6
            """
        ),
        ("user", "Analyze the sentiment of this query: {query}"),
        ("placeholder", "{messages}")

    ]
)

sentiment_analysis = sentiment_analysis_prompt | LLM | StrOutputParser()