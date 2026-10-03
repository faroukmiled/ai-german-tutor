-- SQLite
CREATE TABLE IF NOT EXISTS sessions (
session_id TEXT PRIMARY KEY,
created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS messages(
message_id INTEGER PRIMARY KEY AUTOINCREMENT ,
session_id TEXT REFERENCES sessions(session_id) NOT NULL,
role TEXT CHECK(role IN  ('user','model')) NOT NULL,
message TEXT NOT NULL,
corrected_sentence TEXT,
created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS mistakes (
mistake_id INTEGER PRIMARY KEY AUTOINCREMENT ,
message_id INTEGER REFERENCES messages(message_id) NOT NULL,
category TEXT CHECK(category in ('word_order','case','gender_article',
                      'verb_conjugation','tense','preposition',
                      'spelling','vocabulary','other')) NOT NULL,
original TEXT NOT NULL,
correction TEXT NOT NULL,
explanation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vocabulary(
vocab_id INTEGER PRIMARY KEY AUTOINCREMENT ,
session_id TEXT REFERENCES sessions(session_id) NOT NULL,
word TEXT NOT NULL,
gender TEXT CHECK(gender in ('masculine' , 'feminine' , 'neuter')),
translation TEXT NOT NULL,
UNIQUE(session_id,word)
);