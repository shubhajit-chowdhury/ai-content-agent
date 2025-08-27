import json
import os
from typing import Any
import redis
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
import uvicorn
from pydantic_core import to_jsonable_python
from research_agent import research_agent
from pydantic_ai.messages import ModelMessagesTypeAdapter

# Redis setup
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class TwitterContentRequest(BaseModel):
    post_topic: str
    post_type: str = "post"
    post_context: str

class QueryRequest(BaseModel):
    query: str

api_router = APIRouter()

# Routes
@app.get("/api/hello")
async def hello():
    return {"message": "Hello, World!"}


@app.post("/api/content_creator_agent")
async def content_creator_agent(request: TwitterContentRequest):
    try:
        result = await research_agent.run(
            f'Write a twitter "{request.post_context}" "{request.post_type}" about "{request.post_topic}" '
            f'which follows all the standards of the best content writer. '
            f'Always deliver high quality + value posts. Always double check before giving the post. '
            f'Only return the written content. Nothing more than that.'
        )
        return {"received_data": result.output}
    except Exception as e:
        return {"error": str(e)}


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
    try:
        message_history = load_history("message_history")

        result = await research_agent.run(
            f'Act as an expert director who answers questions and tries to solve business problems. '
            f'Answer the question: "{request.query}". '
            f'Always deliver high quality + value answers. '
            f'Only return the answer, nothing more.',
            message_history=message_history
        )

        save_history("message_history", result.all_messages())

        return {"received_data": result.output}

    except Exception as e:
        return {"error": str(e)}


@app.get("/")
async def root():
    return {"message": "Hello from VercelASGI + FastAPI"}


app.include_router(api_router, prefix="/api")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)