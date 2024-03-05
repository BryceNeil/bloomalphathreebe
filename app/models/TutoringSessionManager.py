import uuid
import json
import os
from groq import Groq
from app.misc.constants import SECRETS


class TutoringSessionManager:
    def __init__(self):
        self.sessions = []
        self.client = Groq(api_key=SECRETS.GROQ_API_KEY)  # Use your Groq API key
        self.model = "mixtral-8x7b-32768"  # Specify your Groq model

    def generate_session_id(self):
        return str(uuid.uuid4())

    async def generate_title_and_subtitle(self, question):
        # Ensure question is a string
        question_str = str(question)
        
        prompt = (
            "Given the text: '{question}', generate a response in the following JSON structure: "
            "{{'title': 'Your Title Here', 'subtitle': 'Your Subtitle Here'}}."
        ).format(question=question_str)

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )

        structured_response = response.choices[0].message.content
        print("DATA TYPE: ", type(structured_response), structured_response)
        response_data = json.loads(structured_response)

        title = response_data.get("title", "Default Session Title")
        subtitle = response_data.get("subtitle", "Default Session Subtitle")

        return title, subtitle


    async def initiate_tutoring_session(self, question):
        session_id = self.generate_session_id()
        title, subtitle = await self.generate_title_and_subtitle(question)

        self.sessions.append({
            "session_id": session_id,
            "question": question,
            "title": title,
            "subtitle": subtitle
        })

        return {
            "session_id": session_id,
            "title": title,
            "subtitle": subtitle,
            "confirmation": "Question received"
        }
