import os
from fastapi import WebSocket, APIRouter
from groq import Groq
from app.misc.constants import SECRETS

class LLMResponseGenerator:
    def __init__(self):
        self.client = Groq(api_key=SECRETS.GROQ_API_KEY)
        self.model = "mixtral-8x7b-32768"

    async def stream_response(self, user_input, websocket: WebSocket):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": user_input}],
                model=self.model,
                stream=True  # Ensure streaming is enabled in the Groq API (if supported)
            )
            async for part in chat_completion.iter_parts():
                await websocket.send_text(part.message.content)  # Stream each part of the response
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            await websocket.send_text("Sorry, I couldn't process your request.")

content_router = APIRouter()
response_generator = LLMResponseGenerator()