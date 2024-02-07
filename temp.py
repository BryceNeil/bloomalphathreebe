from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from app.misc.constants import SECRETS
from temp_draw import generate_drawing_instructions
import json
import asyncio
import random

app = FastAPI()
client = AsyncOpenAI(api_key=SECRETS.OPENAI_KEY)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to generate the chat completion with the entire conversation history
async def generate_chat_completion(websocket: WebSocket, conversation):
    if not isinstance(conversation, list):
        print("Error: Conversation is not a list.")
        return

    try:
        # Construct messages list for GPT-4 based on the conversation history
        messages = [{"role": "system", "content": "You are a helpful and knowledgeable tutor."}]
        messages += [{"role": "user", "content": message} for message in conversation]

        # Send the conversation history to GPT-4
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

        # Process and send responses as they are received
        async for response in response_stream:
            if response.choices:
                for choice in response.choices:
                    if hasattr(choice, 'delta') and choice.delta and hasattr(choice.delta, 'content'):
                        content = choice.delta.content
                        if content:
                            await websocket.send_text(content)
                            conversation.append(content)  # Update conversation with GPT's response

    except Exception as e:
        print(f"Error during chat completion generation: {e}")
        await websocket.send_text(f"Error: {e}")

# WebSocket endpoint for chat completions
@app.websocket("/wschat")
async def chat_completion(websocket: WebSocket):
    await websocket.accept()
    conversation = []

    try:
        initial_question = json.dumps({
            "type": "chat", 
            "content": "What can I help you learn today?"
        })
        await websocket.send_text(initial_question)
        print("Sent initial question to client.")

        while True:
            user_input = await websocket.receive_text()
            print("Received input from client:", user_input)
            conversation.append(user_input)
            await generate_chat_completion(websocket, conversation)

            print("Generating drawing instructions...")
            drawing_instructions = await generate_drawing_instructions(conversation)
            if drawing_instructions:
                print("Drawing instructions received:", drawing_instructions)
                if "drawing_data" in drawing_instructions:
                    print("Preparing drawing data message...")
                    drawing_data_message = json.dumps({
                        "type": "drawingData",
                        "content": drawing_instructions["drawing_data"]
                    })
                    print("Sending drawing data to client.")
                    await websocket.send_text(drawing_data_message)
                else:
                    print("Preparing drawing instruction message...")
                    instruction_message = json.dumps({
                        "type": "drawingInstruction",
                        "content": f"GPT-3: I will now illustrate: {drawing_instructions['drawing_description']}"
                    })
                    print("Sending drawing instructions to client.")
                    await websocket.send_text(instruction_message)
            else:
                print("No drawing instructions were generated.")

    except WebSocketDisconnect:
        print("Client disconnected from chat.")
    except Exception as e:
        print(f"An error occurred: {e}")




@app.websocket("/tutorpointer")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Generate random cursor coordinates
        x = random.randint(0, 800)  # Example range, adjust as needed
        y = random.randint(0, 600)  # Example range, adjust as needed
        await websocket.send_json({"x": x, "y": y})
        await asyncio.sleep(0.5)  # Adjust the frequency of updates as needed




# Run the app using a command like: uvicorn temp:app --reload
