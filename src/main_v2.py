from langchain_core.messages import HumanMessage

from langgraph_logic_v2.graph import graph
from langgraph_logic_v2.utils import _print_event

def main():
    print("Welcome to the Video Game Recommendation Chatbot!")
    print("Ask me for video game recommendations or information about video games.")
    print("Type 'quit' or 'exit' to end the conversation.")

    _printed = set()

    while True:
        user_input = input("User: ")

        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break

        state = {
            "messages": [HumanMessage(content=user_input)],
            "query": user_input,
            "category": "",
            "games": [],
            "details": {},
            "links": [],
            "index": 0,
            "response": []
        }

        print("Chatbot: ")
        for event in graph.stream(state, config=None, stream_mode="values"):
                _print_event(event, _printed)
            
if __name__ == "__main__":
    main()
