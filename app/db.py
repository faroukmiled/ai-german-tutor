import sqlite3
from typing import Optional
from app.schemas import TutorResponse
from pathlib import Path
import os
BASE_DIR = Path(__file__).parent.parent
DB_PATH = os.getenv("TUTOR_DB",BASE_DIR /"tutor.db")
SCHEMA_PATH = BASE_DIR / "schema.sql"
MIGRATIONS = [
     # 1 - learner level
     """ ALTER TABLE sessions ADD COLUMN level TEXT NOT NULL DEFAULT 'A2' CHECK (level IN
('A1', 'A2', 'B1', 'B2'))""",
     # 2 - space repetition
"""ALTER TABLE vocabulary ADD COLUMN box INTEGER NOT NULL DEFAULT 1""",
"""ALTER TABLE vocabulary ADD COLUMN due_at TEXT"""]
REVIEW_INTERVALS_DAYS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def init_db():
     conn = get_connection() 
     try:
        conn.executescript(SCHEMA_PATH.read_text()) 
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        for number,sql in enumerate(MIGRATIONS[version:], start=version + 1):
             conn.execute("BEGIN")
             conn.execute(sql)
             conn.execute(f"PRAGMA user_version = {number}")
             conn.commit()
             print(f"Applied migration {number}")
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
def get_level(session_id:str)->str:
        with get_connection() as conn:
            row = conn.execute("""SELECT level from sessions WHERE session_id = ?""",(session_id,)).fetchone()
            return row[0] if row else "A2"
def set_level(session_id:str, level : str)->str:
        with get_connection() as conn:
            conn.execute("""INSERT OR IGNORE INTO sessions (session_id) VALUES (?)""",(session_id,))
            conn.execute("""UPDATE sessions SET level = ? WHERE session_id = ?""",(level,session_id))
def mistake_stats(session_id:str, days : int = 30) -> list[tuple[str,str]]:
    with get_connection() as conn:
        rows = conn.execute("""SELECT k.category,COUNT(*) AS n FROM mistakes k JOIN messages m ON k.message_id = m.message_id 
                      WHERE m.session_id = ? AND m.created_at>=datetime('now',?)  
                      GROUP BY k.category ORDER BY n DESC 
                      """,(session_id,f"-{days} days")).fetchall()
        return rows 
def weak_categories(session_id:str, top:int=3,min_count = 2) -> list[str]:
     weak_spots = [category for (category,count) in mistake_stats(session_id=session_id) if int(count)>=min_count]
     return weak_spots[:top]
    
def list_vocabulary(session_id:str) -> list[tuple]:
     with get_connection() as conn:
          return conn.execute(
            "SELECT word, gender, translation, box FROM vocabulary "
            "WHERE session_id = ? ORDER BY word COLLATE NOCASE", (session_id,),
            ).fetchall()
def count_due(session_id : str) -> str : 
     with get_connection() as conn:
          return conn.execute("SELECT COUNT(*) FROM vocabulary "
                              "WHERE session_id = ? AND due_at <=datetime('now')",
                              (session_id,)).fetchone()[0]
def next_new_word(session_id: str)-> Optional[tuple]:
     with get_connection() as conn:
        return conn.execute( """
                SELECT vocab_id, word, gender, translation, box FROM vocabulary
                WHERE session_id = ?
                AND (due_at IS NULL OR due_at <= datetime('now')) ORDER BY due_at IS NOT NULL, due_at
                LIMIT 1
                 """,
                (session_id,),
            ).fetchone()
def review_word(session_id:str,vocab_id : int, knew_it):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT box FROM vocabulary WHERE vocab_id = ? AND session_id = ?",
            (vocab_id, session_id),
        ).fetchone()
        if row is None:
             return
        box = min(row[0]+1,5) if knew_it else 1
        days = REVIEW_INTERVALS_DAYS[box]
        conn.execute(
             "UPDATE vocabulary SET box = ?, due_at = datetime('now',?) "
             "WHERE session_id = ? AND vocab_id = ?",
             (box,f"+{days} days",session_id,vocab_id),
        )
     
     

     