from email.mime import audio
import openai
from openai import AsyncOpenAI
from openai import OpenAI
from misc.constants import SECRETS
import subprocess
import io
import httpx
from pydantic import BaseModel

from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import base64
import os
from fastapi import WebSocket, UploadFile
import asyncio
import sounddevice as sd
import wavio



client = AsyncOpenAI(api_key= SECRETS.OPENAI_KEY)

from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play

# Async function to get GPT-4 response with streaming
async def get_gpt_response(text):
    try:
        response_stream = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": text}
            ],
            stream=True,
            temperature=1.1,
            max_tokens=600,
            top_p=1,
            frequency_penalty=0.3,
            presence_penalty=0.5,
        )

        async for response in response_stream:
            if response.choices:
                choice = response.choices[0]
                if choice.delta and choice.delta.content:
                    yield choice.delta.content
                else:
                    yield ""
    except httpx.RemoteProtocolError:
        print("Connection closed unexpectedly by peer during streaming.")
    except Exception as e:
        print(f"Error: {e}")