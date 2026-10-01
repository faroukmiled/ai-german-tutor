from typing import Literal
from pydantic import BaseModel

class Mistake(BaseModel):
    category: Literal['word_order','case','gender_article',
                      'verb_conjugation','tense','preposition',
                      'spelling','vocabulary','other']                             
    original: str                    
    correction: str       
    explanation: str
class VocabEntry(BaseModel):
    word : str
    gender : Literal['masculine' , 'feminine' , 'neuter']|None
    translation : str
class TutorResponse(BaseModel):
    reply : str
    corrected_sentence : str|None
    mistakes : list[Mistake]
    vocabulary : list[VocabEntry]


