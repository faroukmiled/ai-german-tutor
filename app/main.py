import uuid
from typing import Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app import db,ratelimit
from app.tutor import ask_tutor,TutorUnavailable
from app.filters import article
HISTORY_LIMIT = 2
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield
app = FastAPI(lifespan=lifespan)
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["article"] = article
@app.get("/", response_class=HTMLResponse)
def home(request : Request):
    session_id = request.cookies.get("session_id")
    conversation = db.load_conversation(session_id=session_id) if session_id else []
    response = templates.TemplateResponse(
        request, "index.html", {"greeting": "Hallo! Ich bin dein Deutsch-Tutor.",
                                "conversation":conversation,"level":db.get_level(session_id=session_id) if session_id else "A2",
                                "active":"chat"},
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
    if not ratelimit.allow(session_id):
        return HTMLResponse('<p class="notice">Langsam! Bitte warte einen Moment.</p>')
         
    db.ensure_session(session_id=session_id)
    history = db.load_history(session_id=session_id,limit=HISTORY_LIMIT)
    level = db.get_level(session_id=session_id)
    try : 
        tutor_response = ask_tutor(message,history,level,db.weak_categories(session_id=session_id))
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
@app.get("/progress", response_class=HTMLResponse)
def progress(request: Request):
    session_id = request.cookies.get("session_id")
    stats = db.mistake_stats(session_id=session_id) if session_id else []
    total = sum(n for _,n in stats)
    response = templates.TemplateResponse(
        request, "progress.html", {"stats": stats,"total":total,"active":"progress"}
    )
    return response
@app.get("/vocab", response_class=HTMLResponse)
def vocab(request : Request):
     session_id = request.cookies.get("session_id")
     words = db.list_vocabulary(session_id) if session_id else []
     due = db.count_due(session_id) if session_id else 0
     return templates.TemplateResponse(
          request,"vocab.html",{"words":words,"due":due,"active":"vocab"}
     )
@app.get("/review", response_class=HTMLResponse)
def review(request : Request):
     session_id = request.cookies.get("session_id")
     card = db.next_due_word(session_id=session_id) if session_id else None
     return templates.TemplateResponse(
          request,"review.html",{"card":card,"active":"review"}
     )
@app.post("/review/{vocab_id}", response_class=HTMLResponse)
def review_answer(request:Request, vocab_id : int, knew : int = Form()):
    session_id = request.cookies.get("session_id")
    if session_id:
         db.review_word(session_id=session_id,vocab_id=vocab_id,knew_it=bool(knew))
    card = db.next_due_word(session_id=session_id) if session_id else None
    return templates.TemplateResponse(
          request,"partials/card.html",{"card":card}
     )

