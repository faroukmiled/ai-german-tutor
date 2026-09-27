import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]

for model in CANDIDATES:
    try:
        client.models.generate_content(model=model, contents="Hallo")
        print(f"OK      {model}")
    except errors.APIError as e:
        print(f"FAILED  {model}  ({e.code})")