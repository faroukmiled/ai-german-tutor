ARTICLES = {"masculine": "der", "feminine": "die", "neuter": "das"}
from markupsafe import Markup,escape
def article(gender) -> str:
    return ARTICLES.get(gender, "")
def highlight(text, mistakes) -> Markup:
    spans = []
    for m in mistakes:
        original = m["original"] if isinstance(m, dict) else m.original
        start = text.find(original) if original else -1
        if start!=-1:
            spans.append((start,start+len(original)))
    spans.sort()
    j = 0
    parts = []
    pos = 0
    for start,end in spans:
        if (start<pos):
            continue
        parts.append(escape(text[pos:start]))
        parts.append(Markup("<mark>") + escape(text[start:end]) + Markup("</mark>"))
        pos = end
    parts.append(text[pos:])
    return Markup("").join(parts)



