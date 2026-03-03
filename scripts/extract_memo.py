import re
from scripts.utils import norm_phone

EMERGENCY_KEYWORDS = {
    "gas leak / gas smell": ["gas smell", "gas leak", "smell gas"],
    "fire / smoke": ["fire", "smoke"],
    "flooding / burst pipe": ["flood", "burst pipe", "water everywhere"],
    "no heat / no AC": ["no heat", "heater not working", "no ac", "ac not working"],
    "carbon monoxide": ["co alarm", "carbon monoxide"],
}

SERVICE_KEYWORDS = {
    "plumbing": ["plumbing", "leak", "pipe", "drain"],
    "hvac": ["hvac", "heater", "furnace", "ac", "air conditioner"],
    "electrical": ["electrical", "breaker", "power outage", "wiring"],
}

TZ_PAT = re.compile(r"\b(PST|EST|CST|MST|IST|UTC[+-]\d+|America\/[A-Za-z_]+)\b", re.I)
PHONE_PAT = re.compile(r"(\+?\d[\d\-\s\(\)]{8,}\d)")

def extract_company_name(text: str) -> str:
    m = re.search(r"(welcome to|this is|you've reached)\s+([A-Z][A-Za-z0-9&\-\s]{2,60})", text, re.I)
    return (m.group(2).strip() if m else "")

def extract_timezone(text: str) -> str:
    m = TZ_PAT.search(text)
    return (m.group(1).upper() if m else "")

def extract_services(text: str):
    found = set()
    t = text.lower()
    for svc, kws in SERVICE_KEYWORDS.items():
        if any(k in t for k in kws):
            found.add(svc)
    return sorted(found)

def extract_emergencies(text: str):
    found = set()
    t = text.lower()
    for label, kws in EMERGENCY_KEYWORDS.items():
        if any(k in t for k in kws):
            found.add(label)
    return sorted(found)

def extract_phones(text: str):
    phones = []
    for m in PHONE_PAT.finditer(text):
        p = norm_phone(m.group(1))
        if len(p) >= 10 and p not in phones:
            phones.append(p)
    return phones

def extract_business_hours(text: str):
    days = []
    start = ""
    end = ""
    t = text.lower()

    if "mon-fri" in t or "monday" in t and "friday" in t:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    elif "weekdays" in t:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t)
    if m:
        start = f"{m.group(1)}{m.group(3) or ''}".strip()
        end = f"{m.group(4)}{m.group(6) or ''}".strip()

    return {"days": days, "start": start, "end": end}

def build_memo(account_id: str, text: str):
    company = extract_company_name(text)
    tz = extract_timezone(text)
    bh = extract_business_hours(text)
    bh["timezone"] = tz

    services = extract_services(text)
    emergencies = extract_emergencies(text)
    phones = extract_phones(text)

    questions = []
    if not company: questions.append("Need company_name")
    if not bh["days"] or not bh["start"] or not bh["end"]:
        questions.append("Need business_hours (days/start/end)")
    if not tz: questions.append("Need timezone")
    if not emergencies: questions.append("Need emergency_definition")
    if not services: questions.append("Need services_supported")
    if not phones: questions.append("Need routing phone numbers")

    memo = {
        "account_id": account_id,
        "company_name": company,
        "business_hours": bh,
        "office_address": "",
        "services_supported": services,
        "emergency_definition": emergencies,
        "emergency_routing_rules": {
            "contacts": phones,
            "order": phones,
            "fallback": ""
        },
        "non_emergency_routing_rules": {
            "contacts": phones,
            "order": phones,
            "fallback": ""
        },
        "call_transfer_rules": {
            "timeout_seconds": 25,
            "retries": 1,
            "fail_message": ""
        },
        "integration_constraints": [],
        "after_hours_flow_summary": "",
        "office_hours_flow_summary": "",
        "questions_or_unknowns": questions,
        "notes": "Extracted via deterministic rules; blanks mean not present in transcript."
    }

    return memo