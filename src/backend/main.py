from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import HumanMessage
from langgraph_logic.graph import graph
from langgraph_logic.utils import _print_event

app = FastAPI(
    title="Video Game Recommendation Chatbot",
    version="1.0",
    description="An API server to provide personalized video game recommendations."
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust the origin as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

class Input(BaseModel):
    input: str

responses = {}

@app.post("/chat")
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
    response_id = str(len(responses))
    responses[response_id] = []

    async for event in graph.astream(state, config=None, stream_mode="values"):
        output = _print_event(event, _printed)
        if output:
            responses[response_id].append(output)
            print(f"Stored chunk: {output}")  # Debug statement
    responses[response_id].append("[DONE]")
    print("Stored done signal")

    return {"response_id": response_id}

@app.get("/stream_response/{response_id}")
async def stream_response(response_id: str):
    async def generate():
        print(f"Streaming response for ID: {response_id}")
        for chunk in responses.get(response_id, []):
            print(f"Streaming chunk: {chunk}")  # Debug statement
            yield f"data: {chunk}\n\n"
        print("Streaming done signal")
        responses.pop(response_id, None)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
