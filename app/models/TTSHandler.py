# import os
# import io
# from fastapi import WebSocket
# from elevenlabs import generate, stream
# from google.cloud import speech

# class TTSHandler:
#     def __init__(self, elevenlabs_api_key: str):
#         self.api_key = elevenlabs_api_key

#     async def generate_and_stream_audio(self, text, websocket: WebSocket):
#         audio_stream = generate(
#             api_key=self.api_key,
#             text=text,
#             # voice="George",  # Adjust as needed
#             model="eleven_turbo_v2",
#             stream=True
#         )

#         audio_buffer = io.BytesIO()
#         await self.stream_audio_and_extract_timings(audio_stream, audio_buffer, websocket)

#     async def stream_audio_and_extract_timings(self, audio_stream, audio_buffer, websocket: WebSocket):
#         client = speech.SpeechClient()
#         config = speech.RecognitionConfig(
#             encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#             sample_rate_hertz=16000,
#             language_code="en-US",
#             enable_word_time_offsets=True,
#         )

#         # Stream audio to WebSocket and extract timings in real-time
#         async for chunk in audio_stream.iter_bytes():
#             audio_buffer.write(chunk)
#             await websocket.send_bytes(chunk)

#             # Process audio buffer for word timings
#             audio_buffer.seek(0)
#             audio = speech.RecognitionAudio(content=audio_buffer.read())
#             response = await client.recognize(config=config, audio=audio)
#             word_timings = self.extract_word_timings(response)

#             # Stream word timings to WebSocket
#             for word_timing in word_timings:
#                 await websocket.send_json(word_timing)

#             # Clear the buffer for the next audio chunk
#             audio_buffer.seek(0)
#             audio_buffer.truncate()

#     def extract_word_timings(self, response):
#         word_timings = []
#         for result in response.results:
#             for alternative in result.alternatives:
#                 for word_info in alternative.words:
#                     word_timings.append({
#                         "word": word_info.word,
#                         "start_time": word_info.start_time.total_seconds(),
#                         "end_time": word_info.end_time.total_seconds(),
#                     })
#         return word_timings
