from google.genai import types
from google.genai import errors
import os
from google import genai
from app.schemas import TutorResponse
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LEVEL_GUIDANCE = {
    "A1": "Use very short, simple sentences in the present tense and only very common"
"everyday words.",
    "A2": "Use short sentences and common words. Present and perfect tense are fine.",
    "B1": "Use natural everyday German with some subordinate clauses and a wider"
"vocabulary.",
    "B2": "Use natural, fluent German, including idioms and more complex sentence"
"structures.",
}

client = genai.Client(api_key=GEMINI_API_KEY)
MODELS = ["gemini-3.5-flash", "gemini-3.6-flash","gemini-3.7-flash", "gemini-3.8-flash", "gemini-flash-latest"]
BASE_PROMPT = """You are a friendly German tutor chatting with a learner at level {level}.
Language level = {guidance}
Field rules:
- reply: a natural answer in simple German (1-2 sentences) that keeps the conversation going and ends with a question. Do not mention mistakes here.
- corrected_sentence: the learner's full message, corrected. Use null if there are no mistakes.
- mistakes: one entry per separate mistake. Empty list if there are none. Never flag correct German as a mistake.
  - original: the exact wrong words, copied from the learner's message.
  - correction: the corrected words.
  - explanation: one short sentence in English.
  - category: word_order (verb position, V2, verb at the end), case (nominative/accusative/dative/genitive), gender_article (der/die/das, wrong article), verb_conjugation (wrong verb ending), tense (wrong tense, haben vs. sein), preposition (wrong preposition), spelling (typos, capitalisation, umlauts), vocabulary (wrong word choice), other (anything else).
- vocabulary: 0-2 useful words from this exchange that a {level} learner may not know (not basic words like "ich" or "und"). Translation in English. gender only for nouns, null for all other words."""
class TutorUnavailable(Exception):
    pass
def build_system_prompt(level : str = "A2")->str:
    return BASE_PROMPT.format(level = level,guidance = LEVEL_GUIDANCE[level])
def ask_tutor(message: str, history: list, level: str) -> TutorResponse:
    records = [types.Content(role=record[0],parts=[types.Part(text=record[1])]) 
               for record in history]
    records.append(types.Content(role="user",parts=[types.Part(text=message)]))
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=records,
                config=types.GenerateContentConfig(
                        system_instruction=build_system_prompt(level),
                        response_mime_type="application/json",
                        response_schema=TutorResponse,
                        ),
            )
            if response.parsed is None:
                print(f"{model} returned unparseable output")
                continue  
            return response.parsed
        except errors.APIError as e:
            print(f"{model} failed: {e}")
    raise TutorUnavailable