import sqlite3

DB_PATH = "./tutor.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def ensure_session(session_id : str):
    with get_connection() as conn :
        conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,))
def save_message(session_id: str, role : str, message : str):
    with get_connection() as conn :
        conn.execute("INSERT  INTO messages (session_id,role,message) VALUES (?,?,?)", (session_id,role,message))
def load_history(session_id:str):
    with get_connection() as conn :
        return conn.execute("SELECT role,message FROM messages where session_id = ? ORDER BY message_id", (session_id,)).fetchall()
