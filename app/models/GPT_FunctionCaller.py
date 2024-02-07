from openai import AsyncOpenAI
from app.models.Drawing import Drawing
from fastapi import FastAPI
from app.misc.constants import SECRETS
import json
import re

app = FastAPI()
client = AsyncOpenAI(api_key=SECRETS.OPENAI_KEY)

class GPT_FunctionCaller:
    def __init__(self, api_key, drawing_instance):
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key)
        self.drawing = drawing_instance

    async def suggest_function_calls(self, gpt_text: str):
        try:
            # Prompt for action suggestion
            action_prompt = f"Read the following text and suggest a single action ('draw', 'point', or 'circle') that a tutor would perform to help visualize and understand the concept: \"{gpt_text}\""
            action_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": action_prompt}],
                temperature=0.7,
                max_tokens=60,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["\n"]
            )
            action = action_response.choices[0].message.content.strip()

            # Prompt for description based on the suggested action
            description_prompt = f"Given the action '{action}' and the text: \"{gpt_text}\", provide a detailed description for what should be visualized to help understand the concept."
            description_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": description_prompt}],
                temperature=0.7,
                max_tokens=150,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["\n"]
            )
            description = description_response.choices[0].message.content.strip()

            return action, description
        except Exception as e:
            print(f"Error in suggest_function_calls: {e}")
            return None, None

# Example of initializing GPT_FunctionCaller with a Drawing instance
drawing_instance = Drawing(openai_key=SECRETS.OPENAI_KEY, google_api_key=SECRETS.GOOGLE_SEARCH_API_KEY, google_cse_id=SECRETS.GOOGLE_SEARCH_CSE_ID)
gpt_function_caller = GPT_FunctionCaller(api_key=SECRETS.OPENAI_KEY, drawing_instance=drawing_instance)
