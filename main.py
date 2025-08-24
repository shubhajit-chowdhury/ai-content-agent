from contextlib import asynccontextmanager
import json
import os
import redis
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
import uvicorn
from pydantic_core import to_jsonable_python
from research_agent import GetTrendingTweetsDeps, research_agent, ResearcherDeps
from pydantic_ai.messages import ModelMessagesTypeAdapter  

@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize state when app starts
    app.state.message_history = None
    yield
    # cleanup when app stops
    app.state.message_history = None


redis_client = r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)

app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TwitterContentRequest(BaseModel):
    post_topic: str
    post_type: str = "post"
    post_context: str

class QueryRequest(BaseModel):
    query: str


api_router = APIRouter()


@app.get("/api/hello")
async def hello():
    return {"message": "Hello, World!"}


@app.post("/api/content_creator_agent")
async def content_creator_agent(request: TwitterContentRequest):
    result = await research_agent.run(
        f'Write a twitter "{request.post_context}" "{request.post_type}" about "{request.post_topic}" '
        f'which follows all the standards of the best content writer. '
        f'Always deliver high quality + value posts. Always double check before giving the post. '
        f'Only return the written content. Nothing more than that. Do not show any thinking text '
        f'or any other text rather than generated content.'
    )
    return {"received_data": result.output}


@app.post("/api/query_agent")
async def query_agent(request: QueryRequest):

    # Get from Redis
    raw_history = redis_client.get("message_history")
    if raw_history:
        # Decode from bytes → str → Python list
        message_history = ModelMessagesTypeAdapter.validate_python(json.loads(raw_history))
    else:
        message_history = None

    # Run agent
    result = await research_agent.run(
        f'Act as an expert director who answers questions and tries to solve business problems. '
        f'Answer the question: "{request.query}". Make sure to hold yourself from rushing. '
        f'Slow down, think and answer. Always deliver high quality + value answers. '
        f'Always double check before giving the answer. Only return the answer. '
        f'Nothing more than that. Do not show any thinking text or any other text '
        f'rather than generated content.',
        message_history=message_history
    )

    # Serialize before saving to Redis
    convert_message_json_objects = to_jsonable_python(result.all_messages())
    redis_client.set("message_history", json.dumps(convert_message_json_objects))

    return {"received_data": result.output}


app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)