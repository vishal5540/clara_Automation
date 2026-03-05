import os, json, re, hashlib
from datetime import datetime

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_json(path: str, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def write_text(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def norm_phone(s: str) -> str:
    digits = re.sub(r"\D+", "", s or "")
    return digits[-10:] if len(digits) >= 10 else digits

def deterministic_account_id(filename: str) -> str:
    m = re.search(r"(acct_\d+)", filename, re.I)
    if m:
        return m.group(1).lower()
    h = hashlib.sha1(filename.encode("utf-8")).hexdigest()[:6]
    return f"acct_{h}"

def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def safe_get(d, path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur