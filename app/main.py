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
from app.schemas import TutorResponse
from app.db import save_exchange,load_history,ensure_session
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash","gemini-3.7-flash", "gemini-3.8-flash", "gemini-flash-latest"]
SYSTEM_PROMPT = """You are a friendly German tutor chatting with a learner at level A2.
Field rules:
- reply: a natural answer in simple German (1-2 sentences) that keeps the conversation going and ends with a question. Do not mention mistakes here.
- corrected_sentence: the learner's full message, corrected. Use null if there are no mistakes.
- mistakes: one entry per separate mistake. Empty list if there are none. Never flag correct German as a mistake.
  - original: the exact wrong words, copied from the learner's message.
  - correction: the corrected words.
  - explanation: one short sentence in English.
  - category: word_order (verb position, V2, verb at the end), case (nominative/accusative/dative/genitive), gender_article (der/die/das, wrong article), verb_conjugation (wrong verb ending), tense (wrong tense, haben vs. sein), preposition (wrong preposition), spelling (typos, capitalisation, umlauts), vocabulary (wrong word choice), other (anything else).
- vocabulary: 0-2 useful words from this exchange that an A2 learner may not know (not basic words like "ich" or "und"). Translation in English. gender only for nouns, null for all other words."""
class TutorUnavailable(Exception):
    pass
def ask_tutor(message: str, history: list) -> TutorResponse:
    records = [types.Content(role=record[0],parts=[types.Part(text=record[1])]) 
               for record in history]
    records.append(types.Content(role="user",parts=[types.Part(text=message)]))
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=records,
                config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=TutorResponse,
                        ),
            )
            if response.parsed:
                return response.parsed
        except errors.APIError as e:
            print(f"{model} failed: {e}")
    raise TutorUnavailable
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
@app.get("/", response_class=HTMLResponse)
def home(request : Request):
    session_id = request.cookies.get("session_id")
    history = load_history(session_id=session_id)
    response = templates.TemplateResponse(
        request, "index.html", {"greeting": "Hallo! Ich bin dein Deutsch-Tutor.",
                                "history":history},
    )
    if "session_id" not in request.cookies:
        session_id = str(uuid.uuid4())
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return response
@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, message: str = Form(...)):
    session_id = request.cookies.get("session_id")
    if not session_id:
            return HTMLResponse("<p>Bitte lade die Seite neu.</p>")
    ensure_session(session_id=session_id)
    history = load_history(session_id=session_id)
    try : 
        tutor_response = ask_tutor(message,history)
        reply = tutor_response.reply
        save_exchange(session_id, message, tutor_response)
    except TutorUnavailable:
        tutor_response= None
        reply = "Entschuldigung, der Tutor ist gerade überlastet. Bitte versuch es gleich noch einmal."
        
    return templates.TemplateResponse(
        request, "partials/message.html",
        {"user_msg": message, "reply": reply,"learnings": tutor_response},
    )