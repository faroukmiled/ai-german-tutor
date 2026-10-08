import pytest
from fastapi.testclient import TestClient
from app import db,main,ratelimit
from app.schemas import TutorResponse,VocabEntry,Mistake
def fake_tutor(message: str, history: list, level: str, weak_categories : list[str]) -> TutorResponse:
    return TutorResponse(
        reply="Toll! Was isst du gern?",
        corrected_sentence="Ich will eine Pizza essen.",
        mistakes=[
            Mistake(category="gender_article", original="ein Pizza",
                    correction="eine Pizza", explanation="Pizza is feminine."),
        ],
        vocabulary=[VocabEntry(word="Pizza", gender="feminine", translation="pizza")],
        )
@pytest.fixture
def client(tmp_path,monkeypatch):
    ratelimit._requests.clear()
    monkeypatch.setattr(db,"DB_PATH",tmp_path / "test.db")
    monkeypatch.setattr(main,"ask_tutor",fake_tutor)
    with TestClient(main.app) as c:
        c.get("/")
        yield c
        