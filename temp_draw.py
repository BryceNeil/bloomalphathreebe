from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

import json
import traceback

from openai import AsyncOpenAI
from app.misc.constants import SECRETS

from drawing.img_search import search_and_download_image
from drawing.vectorization import vectorize_image

from drawing.img_generate import generate_image_via_dalle

app = FastAPI()
client = AsyncOpenAI(api_key=SECRETS.OPENAI_KEY)

# Initialize the OpenAI API client with your API key

# Function to generate drawing instructions based on the conversation context
# Modify draw_function to decide between web search and DALL-E
async def draw_function(drawing_description, use_dalle=False):
    try:
        if use_dalle:
            image_data = await generate_image_via_dalle(drawing_description)
        else:
            image_data = search_and_download_image(drawing_description)

        vector_elements = vectorize_image(image_data)
        scene_data = {
            "elements": vector_elements,
            "appState": {"viewBackgroundColor": "#ffffff"}
        }
        return scene_data  # Return scene data directly
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



# Function to generate drawing instructions based on the conversation context
async def generate_drawing_instructions(conversation):
    print("CONVERSATION: ", conversation)

    # Updated prompt for GPT to decide between DALL-E and general image search
    # Enhanced prompt for GPT to ensure decision-making on image generation method
    conversation_messages = [
        {"role": "system", "content": "You must respond in JSON format. Assess the conversation and decide if a drawing is needed for educational purposes. Consider the trade-off between the specificity of the depiction and the accuracy of information. If a detailed and custom illustration is required that captures the essence of the discussion, prefer DALL-E. If the subject demands high factual accuracy and is well-represented in existing imagery, opt for a general image search. Your response should include 'draw_status' (true/false), 'drawing_description' (detailed for the chosen method), and 'use_dalle' (true/false). The response format must be: {'draw_status': true/false, 'drawing_description': 'detailed description or empty if not applicable', 'use_dalle': true/false}."},
        {"role": "user", "content": "\n".join(conversation)},
    ]

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=conversation_messages,
            temperature=0.7,
            max_tokens=150,
            stop=None,
        )

        response_string = response.choices[0].message.content
        print("INITIAL JSON RESPONSE: ", response_string)
        json_start_index = response_string.find('{')
        if json_start_index != -1:
            response_json_string = response_string[json_start_index:].replace("'", '"')
            try:
                response_json = json.loads(response_json_string)
                print("JSON CONVERTED: ", response_json)
            except json.JSONDecodeError as e:
                print("Failed to parse JSON:", e)
                return None
        else:
            print("No JSON object found in the response.")
            return None

        if "draw_status" in response_json and "drawing_description" in response_json and "use_dalle" in response_json:
            result = {
                "draw_status": response_json["draw_status"],
                "drawing_description": response_json["drawing_description"],
                "use_dalle": response_json["use_dalle"]
            }
            if result["draw_status"]:
                drawing_data = await draw_function(result["drawing_description"], result["use_dalle"])
                return {"drawing_data": drawing_data}  # Return drawing data
            return result
        else:
            print("Response JSON does not have the expected structure.")
            return None
    except Exception as e:
        print(f"Error during drawing instruction generation: {e}")
        return None
