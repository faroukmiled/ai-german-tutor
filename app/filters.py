ARTICLES = {"masculine": "der", "feminine": "die", "neuter": "das"}

def article(gender) -> str:
    return ARTICLES.get(gender, "")