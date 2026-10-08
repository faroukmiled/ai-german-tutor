import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = """You are a friendly German tutor chatting with a learner at level A2.
- First, reply naturally in simple German to keep the conversation going (1-2 sentences, end with a question).
- Then, if the learner made mistakes, give the corrected sentence and a very short explanation in English.
- If there are no mistakes, don't mention corrections.
- Plain text only. No Markdown, no bold, no bullet points."""

response = client.models.generate_content(
    model=MODEL,
    contents="Ich habe gestern in die Kino gegangen.",
    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
)

print(response.text)