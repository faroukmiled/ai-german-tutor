import sqlite3
from typing import Optional
from app.schemas import TutorResponse
from pathlib import Path
import os
BASE_DIR = Path(__file__).parent.parent
DB_PATH = os.getenv("TUTOR_DB",BASE_DIR /"tutor.db")
SCHEMA_PATH = BASE_DIR / "schema.sql"
     
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def init_db():
     conn = get_connection() 
     try:
        conn.executescript(SCHEMA_PATH.read_text()) 
     finally:
        conn.close()
def ensure_session(session_id : str):
    with get_connection() as conn :
        conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,))
def save_message(session_id: str, role : str, message : str, corrected_sentence:Optional[str] = None) -> int:
    with get_connection() as conn :
        cursor = conn.execute("INSERT  INTO messages (session_id,role,message,corrected_sentence) VALUES (?,?,?,?)", (session_id,role,message,corrected_sentence))
        return cursor.lastrowid
def load_history(session_id:str):
    with get_connection() as conn :
        return conn.execute("SELECT role,message FROM messages where session_id = ? ORDER BY message_id", (session_id,)).fetchall()
def save_exchange(session_id: str, user_message: str, tutor: TutorResponse) -> None:
    with get_connection() as conn :
        user_message_id = conn.execute("INSERT  INTO messages (session_id,role,message,corrected_sentence) VALUES (?,?,?,?)", (session_id,"user",user_message,tutor.corrected_sentence)).lastrowid
        conn.execute("INSERT  INTO messages (session_id,role,message) VALUES (?,?,?)", (session_id,"model",tutor.reply))
        for mistake in tutor.mistakes:
            conn.execute("INSERT INTO mistakes (message_id,category,original,correction,explanation) VALUES (?,?,?,?,?) ",(user_message_id,mistake.category,mistake.original,mistake.correction,mistake.explanation))
        for vocab in tutor.vocabulary:
            conn.execute("INSERT OR IGNORE INTO vocabulary (session_id,word,gender,translation) VALUES (?,?,?,?) ",(session_id,vocab.word,vocab.gender,vocab.translation))
def load_conversation(session_id: str)->list[dict]:
    with get_connection() as conn :
        rows = rows = conn.execute( """
            SELECT m.message_id, m.role, m.message, m.corrected_sentence,
                   k.category, k.original, k.correction, k.explanation
            FROM messages m
            LEFT JOIN mistakes k ON k.message_id = m.message_id WHERE m.session_id = ?
            ORDER BY m.message_id, k.mistake_id
            """,
            (session_id,),
                    ).fetchall()
        conversation = []
        for message_id, role, text, corrected, category, original, correction, explanation in rows:
            if not conversation or conversation[-1]["id"] != message_id: conversation.append({
                            "id": message_id,
                            "role": role,
                            "text": text,
                            "corrected_sentence": corrected,
                            "mistakes": [],
            })
            if category is not None:
                        conversation[-1]["mistakes"].append({
                            "category": category,
                            "original": original,
                            "correction": correction,
                            "explanation": explanation,
            })
        return conversation



            

        

    pass
