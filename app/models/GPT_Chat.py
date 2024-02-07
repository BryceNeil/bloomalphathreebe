from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
from app.misc.constants import SECRETS
from app.models.GPT_FunctionCaller import GPT_FunctionCaller
from app.models.GPT_tts import GPT_tts
from app.models.Drawing import Drawing
import base64
import json
import asyncio
import re
from pydub import AudioSegment
import uuid


app = FastAPI()

# Initialize the AsyncOpenAI client with your API key
client = AsyncOpenAI(api_key=SECRETS.OPENAI_KEY)

class GPT_Chat:
    def __init__(self):
        self.websocket = None  # Initialize WebSocket attribute
        self.conversation = []
        self.speech_enabled = False
        self.audio_playback_complete = asyncio.Event()
        self.audio_playback_complete.set()
        self.drawing_instance = Drawing(openai_key=SECRETS.OPENAI_KEY, google_api_key=SECRETS.GOOGLE_SEARCH_API_KEY, google_cse_id=SECRETS.GOOGLE_SEARCH_CSE_ID)
        self.function_caller = GPT_FunctionCaller(api_key=SECRETS.OPENAI_KEY, drawing_instance=self.drawing_instance)
        self.sentence_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()

    # Other methods remain unchanged

    async def process_sentences_for_speech(self):
        while True:
            sentence = await self.sentence_queue.get()
            if sentence and self.speech_enabled:
                audio_output_file = "audio_output.mp3"
                success = await GPT_tts.text_to_speech(sentence, audio_output_file)
                if success:
                    # Load the audio file
                    audio = AudioSegment.from_file(audio_output_file)
                    # Get the duration in seconds
                    audio_duration = len(audio) / 1000.0
                    
                    audio_base64 = base64.b64encode(open(audio_output_file, "rb").read()).decode('utf-8')
                    # Send the audio to the frontend
                    await self.send_message("speech", audio_base64)
                    # Wait for the exact duration of the audio
                    await asyncio.sleep(audio_duration)
                self.audio_playback_complete.set()

    async def generate_chat_completion_and_speech(self, websocket: WebSocket):
        if not isinstance(self.conversation, list):
            print("Error: Conversation is not a list.")
            return

        try:
            messages = [{"role": "system", "content": "You are a helpful and knowledgeable tutor."}] + \
                       [{"role": "user", "content": message} for message in self.conversation]

            response_stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=1.1,
                max_tokens=600,
                top_p=1,
                frequency_penalty=0.3,
                presence_penalty=0.5,
                stream=True
            )

            full_response_text = ""  # Initialize a string to accumulate the entire response
            sentence_accumulator = ""  # Initialize a string to accumulate sentences for TTS

            async for response in response_stream:
                if response.choices:
                    for choice in response.choices:
                        if hasattr(choice, 'delta') and choice.delta and hasattr(choice.delta, 'content'):
                            gpt_text = choice.delta.content if choice.delta.content is not None else ""
                            if gpt_text:
                                # Stream each token to the front end
                                await self.send_message("token", gpt_text)

                                # Accumulate full response text
                                full_response_text += gpt_text

                                # Accumulate text for a complete sentence for TTS
                                sentence_accumulator += gpt_text
                                if '.' in gpt_text:  # Check for end of a sentence
                                    # Send the complete sentence to the queue for text-to-speech processing
                                    await self.sentence_queue.put(sentence_accumulator)
                                    sentence_accumulator = ""  # Reset accumulator for the next sentence

            # If there's text left in the sentence_accumulator after the loop, process it as well for TTS
            if sentence_accumulator:
                await self.sentence_queue.put(sentence_accumulator)

        except Exception as e:
            print(f"Error during chat and speech generation: {e}")
            await self.send_message("error", str(e))


    async def send_message(self, message_type: str, data: bytes or str, websocket: WebSocket):
        try:
            message = json.dumps({"type": message_type, "data": data})
            await self.websocket.send_text(message)
        except WebSocketDisconnect:
            print("WebSocket disconnected while attempting to send message.")
        except Exception as e:
            print(f"Exception occurred while sending message: {e}")


    @staticmethod
    async def chat_session(self, websocket: WebSocket):
        self.websocket = websocket  # Store the WebSocket connection in the instance
        await self.websocket.accept()
        asyncio.create_task(self.process_sentences_for_speech())

        try:
            while True:
                data = await self.websocket.receive_text()  # Use the stored WebSocket connection
                data_json = json.loads(data)

                # Process received data...

                if data_json.get('type') == 'user':
                    user_message = data_json.get('text')
                    self.conversation.append(user_message)
                    await self.generate_chat_completion_and_speech()  # No need to pass WebSocket

        except WebSocketDisconnect:
            print("Client disconnected from chat")
        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
            await self.websocket.close(code=1001)  # Use the stored WebSocket connection