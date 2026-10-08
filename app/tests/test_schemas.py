from app.schemas import TutorResponse


data = """{
  "reply": "Lecker! Was hast du in der Schule gemacht?",
  "corrected_sentence": "Gestern habe ich einen Apfel gegessen.",
  "mistakes": [
    {"category": "case", "original": "ein Apfel", "correction": "einen Apfel",
     "explanation": "Accusative masculine."}
  ],
  "vocabulary" : []
}"""

r = TutorResponse.model_validate_json(data)
print(r.mistakes[0].category)