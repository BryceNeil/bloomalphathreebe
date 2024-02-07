from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp
import numpy as np
import cv2
from io import BytesIO
import uuid
import json
from openai import AsyncOpenAI

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageDescription(BaseModel):
    description: str

class Drawing:
    def __init__(self, openai_key, google_api_key, google_cse_id):
        self.openai_client = AsyncOpenAI(api_key=openai_key)
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id

    async def decide_generation_method(self, description):
        try:
            prompt = f"Should I use a creative depiction with DALL-E for the following description: '{description}'? Yes or No."
            # Prepare the messages for the chat-based model
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
            # Use the chat completion endpoint
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",  # Ensure this is a chat-compatible model
                messages=messages,
                temperature=0.7,
                max_tokens=60,
                n=1
            )
            # Adjust how you access the response based on the structure provided by the chat completions endpoint
            decision = response.choices[0].message.content.strip().lower()  # Access content directly
            print(f"Decision for '{description}': {decision}")
            return True if "yes" in decision else False
        except Exception as e:
            print(f"Error in deciding generation method: {e}")
            # Default to False (Google Image Search) in case of an error
            return False



    async def generate_image_via_dalle(self, description):
        try:
            styled_prompt = f"{description} - Create a clear, straightforward illustration."
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=styled_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            print(f"Image URL from DALL-E: {image_url}")
            return await self.download_image(image_url)
        except Exception as e:
            print(f"Error in generating image via DALL-E: {e}")
            raise

    async def search_and_download_image(self, description):
        try:
            search_url = f"https://www.googleapis.com/customsearch/v1?q={description}&key={self.google_api_key}&cx={self.google_cse_id}&searchType=image&num=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        image_url = data["items"][0]["link"]
                        print(f"Image URL from Google: {image_url}")
                        return await self.download_image(image_url)
                    else:
                        raise Exception(f"Failed to fetch image from Google, status code: {response.status}")
        except Exception as e:
            print(f"Error in searching and downloading image: {e}")
            raise

    async def download_image(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"Image downloaded from URL: {url}")
                        return BytesIO(await response.read())
                    else:
                        raise Exception(f"Failed to download image from URL: {url}, status code: {response.status}")
        except Exception as e:
            print(f"Error in downloading image: {e}")
            raise

    def vectorize_image(self, image_data):
        nparr = np.frombuffer(image_data.getvalue(), np.uint8)
        print("PROGRESS NP: ", nparr)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print("DECODE: ", img)
        if img is None:
            raise ValueError("Image data could not be decoded. Please check the source of the image data.")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        # Instead of finding contours, use the edge points directly
        y_indices, x_indices = np.where(edges > 0)


        # Generate and return only the coordinates
        coordinates = [{'x': int(x), 'y': int(y)} for x, y in zip(x_indices, y_indices)]
        return coordinates


    

    async def process_drawing_suggestion(self, suggestion):
        try:
            use_dalle = await self.decide_generation_method(suggestion['description'])
            if use_dalle:
                image_data = await self.generate_image_via_dalle(suggestion['description'])
                print(f"Using DALL-E for '{suggestion['description']}'")
            else:
                image_data = await self.search_and_download_image(suggestion['description'])
                print(f"Using Google Image Search for '{suggestion['description']}'")
            elements = self.vectorize_image(image_data)
            print(f"Processed drawing suggestion for '{suggestion['description']}'")

            
            return elements
        except Exception as e:
            print(f"Error in processing drawing suggestion for '{suggestion['description']}': {e}")
            raise
