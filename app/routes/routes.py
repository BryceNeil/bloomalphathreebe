from fastapi import FastAPI, WebSocket, APIRouter, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel, Field

import uuid
from app.misc.constants import SECRETS

from app.models.TutoringSessionManager import TutoringSessionManager
from app.models.LLMResponseGenerator import LLMResponseGenerator
# from app.models.TTSHandler import TTSHandler
from app.models.ContextAnalysisService import  ContextAnalysisService
from app.models.ImageGenerator import ImageGenerator
from app.models.ImagePostProcessor import ImagePostProcessor
# from app.models.IllustrationSynchronizer import IllustrationSynchronizer

from fastapi.middleware.cors import CORSMiddleware




app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Content router setup
content_router = APIRouter(prefix="/api/content")


tutoring_session_manager = TutoringSessionManager()  # Create an instance of the class
response_generator = LLMResponseGenerator()
# tts_handler = TTSHandler()
context_analysis_service = ContextAnalysisService()
image_generator = ImageGenerator()
image_post_processor = ImagePostProcessor()

# Assume visual_components is a dictionary where keys are words and values are visual component instructions
# visual_components = {
#     "keyword1": {"type": "circle", "coordinates": {"x": 100, "y": 100}, "radius": 50},
#     "keyword2": {"type": "rectangle", "coordinates": {"x": 200, "y": 200}, "width": 100, "height": 50},
#     # Add more mappings as needed
# }
# illustration_synchronizer = IllustrationSynchronizer(visual_components)


# "TEMP"
# image_url = "http://example.com/image.jpg"
# vector_elements = image_post_processor.process_image(image_url)




class Question(BaseModel):
    question_text: str 

class LLMResponse(BaseModel):
    session_id: str
    response: str

class UserInput(BaseModel):
    text: str

class ImageRequest(BaseModel):
    prompts: List[str]

class ImageResponse(BaseModel):
    images: List[str]  # URLs to the generated images
    metadata: List[Dict[str, Any]]  # Metadata with values of any type

# Define the response model to include the processed image elements
class ImageElement(BaseModel):
    type: str
    id: str
    x: int
    y: int
    strokeColor: str
    width: int
    height: int

class ProcessedImageResponse(BaseModel):
    elements: List[ImageElement]

class CursorAction(BaseModel):
    action: str  # "highlight" or "point"
    coordinates: dict  # {"x": int, "y": int}

# Define your data models here
# For example, a model for the question data might look like:
# class Question(BaseModel):
#     question_text: str

"""CONTENT ROUTES"""

"STATUS: COMPLETE"
@content_router.post("/submit-question/")
async def submit_question(question: Question):
    # Await the asynchronous initiate_tutoring_session method
    response = await tutoring_session_manager.initiate_tutoring_session(question.question_text)
    return response

"STATUS: "
@content_router.websocket("/ws/generate-response/")
async def generate_response(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            user_input = data.get("question_text")
            session_id = data.get("session_id")
            if user_input is not None:
                await response_generator.stream_response(user_input, websocket)
            else:
                await websocket.send_text("Missing 'question_text' in received data.")
    except WebSocketDisconnect:
        print(f"WebSocket disconnected")
    except Exception as e:
        print(f"Error during WebSocket communication: {e}")
        await websocket.send_text("An error occurred, please try again.")

# @content_router.websocket("/ws/tts/")
# async def tts_and_highlighting(websocket: WebSocket):
#     await websocket.accept()
#     tts_handler = TTSHandler(elevenlabs_api_key=SECRETS.e)
    
#     while True:
#         text = await websocket.receive_text()
#         await tts_handler.generate_and_stream_audio(text, websocket)

@content_router.post("/context-analysis/")
async def context_analysis_endpoint(user_input: UserInput):
    try:
        prompts = await context_analysis_service.process_input(user_input.text)
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@content_router.post("/generate-image/", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """
    Endpoint to generate fake images based on the provided prompts.
    """
    return await image_generator.generate_images(request.prompts)

@content_router.post("/process-image/", response_model=ProcessedImageResponse)
async def process_image_endpoint(request: ImageRequest):
    # Assuming the first prompt in the list is the image URL to be processed
    image_url = request.prompts[0] if request.prompts else None
    
    # Handle case where no prompts are provided
    if not image_url:
        return ProcessedImageResponse(elements=[])

    vector_elements = await image_post_processor.process_image(image_url)
    return ProcessedImageResponse(elements=vector_elements)


# @content_router.websocket("/ws/sync-illustration/")
# async def sync_illustration(websocket: WebSocket):
#     await illustration_synchronizer.synchronize_illustration(websocket)

# @content_router.post("/ai-cursor-control/")
# async def ai_cursor_control(canvas_state: dict, spoken_text: str, component_metadata: List[dict]):
#     # Assess the canvas and contextually highlight or point to components
#     # Return dummy cursor action for demonstration
#     return CursorAction(action="highlight", coordinates={"x": 50, "y": 50})

# Note: You would need to implement the actual logic for interacting with the LLM, TTS, Stable Diffusion, and handling the dynamic illustration and AI-controlled cursor based on the project's specific requirements.


# Include the content router in the main app
app.include_router(content_router)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)