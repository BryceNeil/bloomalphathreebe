from uuid import UUID
from fastapi import FastAPI, APIRouter, Depends, Form, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from app.misc.utils import get_profile, validate_token, User as UserProfile
from app.models.GPT_Chat import GPT_Chat
# from app.models.GPT_Vision import GPT
from app.models.User import User
from app.schemas.User import UserLoginData
from app.misc.constants import SECRETS
from app.models.Drawing import Drawing
from app.models.GPT_FunctionCaller import gpt_function_caller

from uuid import uuid4



from fastapi import FastAPI, HTTPException, APIRouter, Form, WebSocket
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from typing import Dict, Any


app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage for coordinates, using session_id as key
coordinates_storage: Dict[str, Any] = {}


# Content router setup
content_router = APIRouter(prefix="/api/content")

class ChatMessage(BaseModel):
    message: str

class DrawingSuggestion(BaseModel):
    description: str


"""CONTENT ROUTES"""

@content_router.websocket("/wschat")
async def chat_completion(websocket: WebSocket):
    chat_instance = GPT_Chat()  # Create an instance of GPT_Chat
    await chat_instance.chat_session(websocket)  # Call chat_session on the instance


# Endpoint for text-to-speech synthesis
@content_router.post("/chat/audio")
async def synthesize_speech(text: str = Form(...)):
    return StreamingResponse(await GPT.gpt_audio_bytes(text), media_type="audio/mpeg")

# Endpoint to determine the action and description
@content_router.post("/action-determination")
async def determine_action(chat_message: ChatMessage):
    # Logic to determine action and description
    # For example, use GPT_FunctionCaller.suggest_function_calls
    action, description = await gpt_function_caller.suggest_function_calls(chat_message.message)
    return {"action": action, "description": description}

@app.post("/generate-coordinates")
async def generate_coordinates(suggestion: DrawingSuggestion):
    # Instantiate your Drawing class (ensure it's initialized properly)
    drawing_instance = Drawing(openai_key="your_openai_key", google_api_key="your_google_api_key", google_cse_id="your_google_cse_id")
    
    # Use the description to process the drawing suggestion
    coordinates = await drawing_instance.process_drawing_suggestion(suggestion)
    
    # Generate a unique session ID and store the coordinates
    session_id = str(uuid4())
    coordinates_storage[session_id] = coordinates
    
    # Return session ID and a flag indicating a drawing is needed
    return {"session_id": session_id, "draw": True}

@app.get("/coordinates/{session_id}")
async def get_coordinates(session_id: str):
    if session_id not in coordinates_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return coordinates_storage[session_id]

# Register content router with the main app
app.include_router(content_router)










"""AUTH ROUTES"""


auth_router = APIRouter(prefix="/api/auth")


@auth_router.get('/profile', dependencies=[Depends(validate_token)])
async def get_token(profile: UserProfile = Depends(get_profile)):
    return profile


@auth_router.post('/login')
async def login_user(login_info: UserLoginData):
    return await User.login(login_info)


@auth_router.post('/signup')
async def create_user(login_info: UserLoginData):
    return await User.create_user(login_info)


"""MISC ROUTES"""
