from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from langchain_core.messages import HumanMessage
from langgraph_logic.graph import graph
from langgraph_logic.utils import _print_event

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

responses = {}

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
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

    def generate():
        for event in graph.stream(state, config=None, stream_mode="values"):
            output = _print_event(event, _printed)
            if output:
                responses[response_id].append(output)
                print(f"Sending chunk: {output}")  # Debug statement
                yield f"data: {output}\n\n"
        print("Sending done signal")
        yield "data: [DONE]\n\n"  # Signal the end of the stream
    
    return jsonify({"response_id": response_id})

@app.route("/stream_response/<response_id>", methods=["GET"])
def stream_response(response_id):
    def generate():
        print(f"Streaming response for ID: {response_id}")
        for chunk in responses.get(response_id, []):
            print(f"Streaming chunk: {chunk}")  # Debug statement
            yield f"data: {chunk}\n\n"
        print("Streaming done signal")
        yield "data: [DONE]\n\n"
        del responses[response_id]

    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True, port=8000)
