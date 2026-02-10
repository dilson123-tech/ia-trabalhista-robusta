import re
from typing import Any

_RE_EMAIL = re.compile(r"([A-Z0-9._%+-]+)@([A-Z0-9.-]+\.[A-Z]{2,})", re.I)
_RE_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
_RE_PHONE = re.compile(r"\b\+?55\s?\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b|\b\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b")

def redact_text(s: str) -> str:
    s = _RE_EMAIL.sub("***@***", s)
    s = _RE_CPF.sub("***CPF***", s)
    s = _RE_PHONE.sub("***TEL***", s)
    return s

def redact(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: redact(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj
