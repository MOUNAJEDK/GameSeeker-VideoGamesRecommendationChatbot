from langchain_core.messages import HumanMessage, AIMessage
from langgraph_logic.graph import graph

from dotenv import load_dotenv
load_dotenv()

def main():
    print("Welcome to the Video Game Recommendation Chatbot!")
    print("Ask me for video game recommendations or information about video games.")
    print("Type 'quit' or 'exit' to end the conversation.")
    
    while True:
        user_input = input("User: ")
        
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break

        state = {
            "messages": [HumanMessage(role="user", content=user_input)],
            "query": user_input,
            "relevant": False,
            "games": [],
            "details": {},
            "response": ""
        }

        # for event in graph.stream(state, {"recursion_limit": 150}):
        #     for value in event.values():
        #         if isinstance(value["messages"][-1], AIMessage):
        #             print("Assistant:", value["messages"][-1].content)

        output = graph.invoke(state)
        print("Assistant:", output["response"])

if __name__ == "__main__":
    main()