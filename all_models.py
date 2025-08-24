from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dotenv import load_dotenv
import os

load_dotenv()

model_1 = GeminiModel(os.getenv("CHAT_MODEL"), provider=GoogleGLAProvider(api_key=os.getenv("API_KEY_1")))

model_2 = GeminiModel(os.getenv("CHAT_MODEL"), provider=GoogleGLAProvider(api_key=os.getenv("API_KEY_2")))


get_model = FallbackModel(
    model_1,
    model_2,
)