from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
import openai

from app.misc.constants import SECRETS  # Import the OpenAI library

# Define your APIRouter
content_router = APIRouter()

# Define the request and response data models
class ImageRequest(BaseModel):
    prompts: List[str]

class ImageResponse(BaseModel):
    images: List[str]  # URLs to the generated images
    metadata: List[Dict[str, Any]]  # Corrected to use Any from typing


class ImageGenerator:
    def __init__(self):
        # Initialize the OpenAI client with your API key
        self.client = openai.OpenAI(api_key=SECRETS.OPENAI_KEY)

    async def generate_images(self, prompts: List[str]) -> ImageResponse:
        """
        Generate images based on the provided prompts using DALL·E.
        """
        images = []
        metadata = []
        for prompt in prompts:
            # Generate an image for each prompt
            response = self.client.images.generate(
                model="dall-e-3",  # Specify the DALL·E model version
                prompt=prompt,
                size="1024x1024",  # Image size
                quality="standard",  # Image quality
                n=1,  # Number of images to generate
            )
            # Assuming the API returns a URL to the generated image
            image_url = response.data[0].url
            image_metadata = {
                "description": f"Generated image for prompt: {prompt}",
                "url": image_url
            }
            images.append(image_url)  # Store the URL instead of base64 data
            metadata.append(image_metadata)
        
        return ImageResponse(images=images, metadata=metadata)
