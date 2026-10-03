import uuid
from typing import Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app import db
from app.tutor import ask_tutor,TutorUnavailable

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")
@app.get("/", response_class=HTMLResponse)
def home(request : Request):
    session_id = request.cookies.get("session_id")
    conversation = db.load_conversation(session_id=session_id) if session_id else []
    response = templates.TemplateResponse(
        request, "index.html", {"greeting": "Hallo! Ich bin dein Deutsch-Tutor.",
                                "conversation":conversation,"level":db.get_level(session_id=session_id) if session_id else "A2"},
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
    db.ensure_session(session_id=session_id)
    history = db.load_history(session_id=session_id)
    level = db.get_level(session_id=session_id)
    try : 
        tutor_response = ask_tutor(message,history,level)
        reply = tutor_response.reply
        db.save_exchange(session_id, message, tutor_response)
    except TutorUnavailable:
        tutor_response= None
        reply = "Entschuldigung, der Tutor ist gerade überlastet. Bitte versuch es gleich noch einmal."
        
    return templates.TemplateResponse(
        request, "partials/message.html",
        {"user_msg": message, "reply": reply,"learnings": tutor_response},
    )
@app.post("/level", response_class=HTMLResponse)
def change_level(request: Request, level: Literal["A1", "A2", "B1", "B2"] = Form(...)):
    session_id = request.cookies.get("session_id")
    if not session_id:
         return HTMLResponse("Bitte lade die Seite neu.")
    db.set_level(session_id=session_id,level=level)
    return HTMLResponse(f"Niveau: {level} ✓")