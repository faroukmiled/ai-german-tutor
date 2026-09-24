from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
@app.get("/", response_class=HTMLResponse)
def home(request : Request):
    return templates.TemplateResponse(
        request, "index.html", {"greeting": "Hallo! Ich bin dein Deutsch-Tutor."}
    )
@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, message: str = Form(...)):
    reply = f"Echo: {message}"
    return templates.TemplateResponse(
        request, "partials/message.html",
        {"user_msg": message, "reply": reply},
    )