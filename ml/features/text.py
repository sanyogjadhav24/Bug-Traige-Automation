import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)   # HTML
    text = re.sub(r"```[\s\S]*?```", " ", text)  # code fences
    text = re.sub(r"[^a-z0-9\s\.\-_/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
