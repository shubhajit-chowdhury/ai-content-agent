import json
import os
from typing import Any
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai import Agent
import redis
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
import uvicorn
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter


redis_client = r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str




chat_model = GeminiModel(os.getenv("CHAT_MODEL"), provider=GoogleGLAProvider(api_key=os.getenv("API_KEY")))

research_agent = Agent(
    chat_model,
    system_prompt='Act as an expert director who answers questions and tries to solve business problems.',

    )


api_router = APIRouter()

def save_history(key: str, messages: Any) -> None:
    redis_client.set(key, json.dumps(to_jsonable_python(messages)))

def load_history(key: str) -> Any:
    history_raw = redis_client.get(key)
    if not history_raw:
        return None
    
    if isinstance(history_raw, bytes):
        history_raw = history_raw.decode("utf-8")

    history_json = json.loads(history_raw)
    return ModelMessagesTypeAdapter.validate_python(history_json)

@app.post("/api/query_agent")
async def query_agent(request: QueryRequest):

    message_history = load_history("message_history")
    print(type(message_history))

    result = await research_agent.run(
        f'Act as an expert director who answers questions and tries to solve business problems. '
        f'Answer the question: "{request.query}". Make sure to hold yourself from rushing. '
        f'Slow down, think and answer. Always deliver high quality + value answers. '
        f'Always double check before giving the answer. Only return the answer. '
        f'Nothing more than that. Do not show any thinking text or any other text '
        f'You have access to your previous conversations. '
        f'Use them to answer the question if needed. If you do not know the answer',
        message_history=message_history
    )

    save_history("message_history", result.all_messages())

    return {"received_data": result.output}


app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)