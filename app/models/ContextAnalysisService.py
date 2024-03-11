from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import json
from typing import List, Tuple
import re

from groq import AsyncGroq  # Ensure you're using the async Groq client
from app.misc.constants import SECRETS  # Assuming import of your secrets or configuration module

app = FastAPI()

class SentenceAnalysis(BaseModel):
    sentence: str
    needs_illustration: bool
    illustration_prompt: str = ""

class ContextAnalysisService:
    def __init__(self):
        self.client = AsyncGroq(api_key=SECRETS.GROQ_API_KEY)
        self.model = "mixtral-8x7b-32768"  # Specify the LLM model

    async def process_input(self, user_input: str):
        sentences = self.split_into_sentences(user_input)
        analysis_results = []
        for sentence in sentences:
            needs_illustration = await self.decide_if_needs_illustration(sentence)
            if needs_illustration:
                illustration_prompt = await self.generate_illustration_prompt(sentence)
                analysis_results.append(SentenceAnalysis(sentence=sentence, needs_illustration=True, illustration_prompt=illustration_prompt))
            else:
                analysis_results.append(SentenceAnalysis(sentence=sentence, needs_illustration=False))
        return analysis_results

    def split_into_sentences(self, text: str) -> List[str]:
        # Simple method to split text into sentences. Consider using a more sophisticated NLP tool for better accuracy.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        return sentences

    async def decide_if_needs_illustration(self, sentence: str) -> bool:
        # Enhanced prompt to guide the LLM in decision making
        prompt = (
            f"Given the sentence: \"{sentence}\", "
            "consider if it contains elements such as vivid imagery, complex concepts that are clearer visually, "
            "or describes actions and scenes that are significantly enhanced by a visual representation. "
            "Does this sentence justify the creation of an illustration to add value or aid understanding? "
            "Respond with 'true' to recommend an illustration or 'false' if it's unnecessary."
        )
        response = await self.query_llm(prompt)

        # Default bias towards creating an image, looking for explicit 'no' to opt out
        normalized_response = response.strip().lower()
        # Explicit cues for when an illustration is not necessary or doesn't add value
        no_cues = ["no", "not necessary", "unnecessary", "does not", "isn't needed", "isn't necessary", "false"]

        # Return False only if the response explicitly advises against an illustration
        return not any(cue in normalized_response for cue in no_cues)


    async def generate_illustration_prompt(self, sentence: str) -> str:
        prompt = f"Generate a detailed description for an illustration based on the following sentence: \"{sentence}\""
        response = await self.query_llm(prompt)
        return response

    async def query_llm(self, prompt: str) -> str:
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                stream=False
            )
            if chat_completion.choices:
                return chat_completion.choices[0].message.content
            else:
                print("No choices returned by the LLM.")
        except Exception as e:
            print(f"Error querying LLM: {e}")
        return ""

context_analysis_service = ContextAnalysisService()
