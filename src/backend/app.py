import asyncio
import nest_asyncio

import markdown2

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage
from langgraph_logic.graph import graph
from langgraph_logic.utils import _print_event

if asyncio.get_event_loop().is_closed():
    asyncio.set_event_loop(asyncio.ProactorEventLoop())
else:
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

nest_asyncio.apply()

app = FastAPI(
    title="Video Game Recommendation Chatbot",
    version="1.0",
    description="An API server to provide personalized video game recommendations."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust the origin as per your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

class Input(BaseModel):
    input: str

class Output(BaseModel):
    output: List[str]

def format_message(content: str) -> str:
    # Convert markdown to HTML
    html_content = markdown2.markdown(content)
    
    # Replace newlines with <br> tags for proper line breaks
    html_content = html_content.replace('\n', '<br>')
    
    return html_content

@app.post("/chat", response_model=Output)
async def chat_endpoint(request: Request):
    data = await request.json()
    user_input = data.get("input")

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

    _printed = set()
    response_list = []

    async for event in graph.astream(state, config={"recursion_limit": 50}, stream_mode="values"):
        output = _print_event(event, _printed)
        if output:
            formatted_output = format_message(output)
            response_list.append(formatted_output)

    combined_response = " ".join(response_list)

    return {"output": [combined_response]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)