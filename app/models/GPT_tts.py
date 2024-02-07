import re
from openai import AsyncOpenAI
from app.misc.constants import SECRETS

client = AsyncOpenAI(api_key=SECRETS.OPENAI_KEY)

class GPT_tts:

    @staticmethod
    async def text_to_speech(text: str, output_file: str):
        try:
            # Split the input text into sentences using regular expressions
            sentences = re.split(r'(?<=[.!?])\s', text)

            # Initialize an empty list to store audio segments for each sentence
            audio_segments = []

            for sentence in sentences:
                if sentence.strip():
                    tts_response = await client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=sentence
                    )

                    # Access the binary content of the response
                    audio_data = tts_response.content

                    # Append the audio segment to the list
                    audio_segments.append(audio_data)

            # Combine audio segments to create the final audio file
            combined_audio_data = b''.join(audio_segments)

            # Write the combined binary content to the output file
            with open(output_file, 'wb') as f:
                f.write(combined_audio_data)

            return True  # Indicate successful generation

        except Exception as e:
            print(f"An error occurred in text-to-speech: {e}")
            return False
