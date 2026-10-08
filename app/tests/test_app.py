from app import db,main
from app.tutor import TutorUnavailable

def test_home_sets_session_cookie(client):
    assert "session_id" in client.cookies

def test_chat_saves_whole_exchange(client):
    response = client.post("/chat", data={"message": "Ich will essen ein Pizza"})
    assert response.status_code ==200
    conversation = db.load_conversation(session_id=client.cookies["session_id"])
    assert [m["role"] for m in conversation]==["user","model"]
    assert conversation[0]["mistakes"][0]["category"] == "gender_article"
    assert conversation[1]["mistakes"] == []

def test_refresh_shows_saved_corrections(client):
    client.post("/chat", data={"message": "Ich will essen ein Pizza"}) 
    assert "Korrektur:" in client.get("/").text

def test_failed_tutor_saves_nothing(client, monkeypatch):
    def broken(*args, **kwargs):
        raise TutorUnavailable
    monkeypatch.setattr(main,"ask_tutor",broken)
    response = client.post("/chat", data={"message": "Hallo"})
    assert "Entschuldigung" in response.text
    assert db.load_conversation(client.cookies["session_id"])==[]

def test_history_limit_keeps_latest_pairs(client):
    session_id = client.cookies["session_id"]
    db.ensure_session(session_id=session_id)
    for i in range(30):
        db.save_message(session_id, "user" if i % 2 == 0 else "model", f"msg {i}")
    db.load_history(session_id,limit=4) == [
        ("user","msg 26"),("model","msg 27"),("user","msg 28"),("model","msg 29")
    ]

def test_level_change(client):
    session_id = client.cookies["session_id"]
    client.post("/level", data={"level": "B1"})
    assert db.get_level(session_id=session_id)=="B1"
    assert client.post("/level", data={"level": "C9"}).status_code == 422

def test_cannot_review_someone_elses_word(client):
    client.post("/chat", data={"message": "Ich will essen ein Pizza"})
    vocab_id = db.next_due_word(client.cookies["session_id"])[0]
    db.review_word("someone-else", vocab_id, knew_it=True)
    assert db.list_vocabulary(client.cookies["session_id"])[0][3] == 1

def test_rate_limit(client):
    for _ in range(10):
        client.post("/chat", data={"message": "Hallo"})
    assert "Langsam" in client.post("/chat", data={"message": "Hallo"}).text
    