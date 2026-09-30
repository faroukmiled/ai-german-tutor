import uuid
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
import os
from google import genai
from google.genai import types
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash","gemini-3.7-flash", "gemini-3.8-flash", "gemini-flash-latest"]
SYSTEM_PROMPT = """You are a friendly German tutor chatting with a learner at level A2.
- First, reply naturally in simple German to keep the conversation going (1-2 sentences, end with a question).
- Then, if the learner made mistakes, give the corrected sentence and a very short explanation in English.
- If there are no mistakes, don't mention corrections.
- Plain text only. No Markdown, no bold, no bullet points."""
histories = {}
def ask_tutor(message: str, history: list) -> str:
    history.append(types.Content(role="user", parts=[types.Part(text=message)]))
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=history,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))
            return response.text
        except errors.APIError as e:
            print(f"{model} failed: {e}")
    history.pop()
    return "Entschuldigung, der Tutor ist gerade überlastet. Bitte versuch es gleich noch einmal."
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
@app.get("/", response_class=HTMLResponse)
def home(request : Request):
    response = templates.TemplateResponse(
        request, "index.html", {"greeting": "Hallo! Ich bin dein Deutsch-Tutor."}
    )
    session_id = str(uuid.uuid4())
    if "session_id" not in request.cookies:
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    histories[session_id] = []
    return response
@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, message: str = Form(...)):
    session_id = request.cookies.get("session_id")
    history = histories.setdefault(session_id, [])
    reply = ask_tutor(message,history)
    return templates.TemplateResponse(
        request, "partials/message.html",
        {"user_msg": message, "reply": reply},
    )