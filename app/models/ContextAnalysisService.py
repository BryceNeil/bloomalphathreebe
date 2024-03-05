# import json
# from typing import List
# from fastapi import WebSocket, APIRouter, WebSocketDisconnect
# from groq import Groq  # Assuming Groq client import
# from app.misc.constants import SECRETS  # Assuming import of your secrets or configuration module

# class ContextAnalysisService:
#     def __init__(self):
#         self.client = Groq(api_key=SECRETS.GROQ_API_KEY)
#         self.model = "mixtral-8x7b-32768"  # Specify the LLM model

#     async def handle_websocket_connection(self, websocket: WebSocket):
#         await websocket.accept()
#         while True:
#             try:
#                 user_input = await websocket.receive_text()
#                 await self.process_input_and_generate_prompts(user_input, websocket)
#             except WebSocketDisconnect:
#                 print("Client disconnected")
#                 break
#             except Exception as e:
#                 await websocket.send_text(f"Error processing input: {str(e)}")
#                 continue

#     async def process_input_and_generate_prompts(self, user_input: str, websocket: WebSocket):
#         key_phrases = await self.extract_key_phrases(user_input)
#         for phrase in key_phrases:
#             description = await self.generate_description_for_phrase(phrase)
#             prompt = self.craft_prompt_for_stable_diffusion(description)
#             await websocket.send_json({"prompt": prompt})

#     async def extract_key_phrases(self, text: str) -> List[str]:
#         prompt = f"Please analyze the following text and list the key phrases in the format: {json.dumps({'key_phrases': ['phrase1', 'phrase2']})}\n{text}"
#         response = await self.query_llm(prompt)
#         if response:
#             try:
#                 key_phrases = json.loads(response).get("key_phrases", [])
#                 return key_phrases
#             except json.JSONDecodeError:
#                 print("Failed to decode JSON response for key phrases.")
#         return []

#     async def generate_description_for_phrase(self, phrase: str) -> str:
#         prompt = f"Provide a detailed description for the phrase '{phrase}' in the format: {json.dumps({'description': 'A detailed description here.'})}"
#         response = await self.query_llm(prompt)
#         if response:
#             try:
#                 description = json.loads(response).get("description", "")
#                 return description
#             except json.JSONDecodeError:
#                 print("Failed to decode JSON response for description.")
#         return ""

#     def craft_prompt_for_stable_diffusion(self, description: str) -> str:
#         return f"Create an illustration of: {description}"

#     async def query_llm(self, prompt: str) -> str:
#         try:
#             chat_completion = self.client.chat.completions.create(
#                 messages=[{"role": "user", "content": prompt}],
#                 model=self.model,
#                 stream=False  # Assume non-streaming for structured response
#             )
#             response = await chat_completion.wait()  # Wait for the complete response
#             return response.message.content  # Assume the last message contains the desired structured content
#         except Exception as e:
#             print(f"Error querying LLM: {e}")
#         return ""
