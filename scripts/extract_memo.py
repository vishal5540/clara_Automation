import re
from scripts.utils import norm_phone

# ----------------------------
# Patterns
# ----------------------------

TZ_PAT = re.compile(r"\b(PST|EST|CST|MST|IST|UTC[+-]\d+|America\/[A-Za-z_]+)\b", re.I)
PHONE_PAT = re.compile(r"(\+?\d[\d\-\s\(\)]{8,}\d)")

# cues that confirm explicit information
EXPLICIT_EMERGENCY_CUES = [
    "emergency",
    "emergencies include",
    "treat as emergency",
    "after hours emergency"
]

EXPLICIT_HOURS_CUES = [
    "business hours",
    "open from",
    "open",
    "monday",
    "mon-fri",
    "weekdays"
]

EXPLICIT_ROUTING_CUES = [
    "transfer",
    "route",
    "forward",
    "dispatch",
    "on-call"
]

EXPLICIT_CONSTRAINT_CUES = [
    "never",
    "do not",
    "must not",
    "servicetrade",
]

# ----------------------------
# Service detection (tighter)
# ----------------------------

SERVICE_KEYWORDS = {
    "plumbing": ["plumbing"],
    "hvac": ["hvac"],
    "electrical": ["electrical"],
    "fire protection": [
        "sprinkler",
        "fire alarm",
        "extinguisher",
        "fire protection"
    ]
}

# ----------------------------
# Emergency detection
# ----------------------------

EMERGENCY_KEYWORDS = {
    "sprinkler leak": ["sprinkler leak", "water flowing", "burst pipe"],
    "fire alarm triggered": ["fire alarm", "alarm triggered"],
    "fire / smoke": ["fire", "smoke"],
    "gas leak": ["gas smell", "gas leak"]
}

# ----------------------------
# Helpers
# ----------------------------

def _snippet(text, idx, span=90):
    start = max(0, idx - span)
    end = min(len(text), idx + span)
    return text[start:end].replace("\n", " ").strip()


def _find_evidence(text, patterns):
    t = text.lower()
    for p in patterns:
        i = t.find(p)
        if i != -1:
            return _snippet(text, i)
    return ""


# ----------------------------
# Extraction functions
# ----------------------------

def extract_company_name(text):

    m = re.search(
        r"(welcome to|this is|you've reached)\s+([A-Z][A-Za-z0-9&\-\s]{2,60})",
        text,
        re.I
    )

    if m:
        return m.group(2).strip(), _snippet(text, m.start(2))

    return "", ""


def extract_timezone(text):

    m = TZ_PAT.search(text)

    if m:
        return m.group(1).upper(), _snippet(text, m.start(1))

    return "", ""


def extract_services(text, strict=True):

    t = text.lower()

    services = []
    evidence = {}

    for service, keywords in SERVICE_KEYWORDS.items():

        for k in keywords:

            idx = t.find(k)

            if idx != -1:

                if service not in services:
                    services.append(service)
                    evidence[service] = _snippet(text, idx)

                break

    return services, evidence


def extract_emergencies(text, strict=True):

    t = text.lower()

    # if strict:
    #     cue = _find_evidence(text, EXPLICIT_EMERGENCY_CUES)

    #     if not cue:
    #         return [], {}

    found = []
    evidence = {}

    for label, keywords in EMERGENCY_KEYWORDS.items():

        for k in keywords:

            idx = t.find(k)

            if idx != -1:

                if label not in found:
                    found.append(label)
                    evidence[label] = _snippet(text, idx)
                break

    return found, evidence


def extract_phones(text):

    phones = []
    evidence = {}

    for m in PHONE_PAT.finditer(text):

        raw = m.group(1)
        p = norm_phone(raw)

        if len(p) >= 10 and p not in phones:
            phones.append(p)
            evidence[p] = _snippet(text, m.start(1))

    return phones, evidence


def extract_business_hours(text, strict=True):

    t = text.lower()

    if strict:

        cue = _find_evidence(text, EXPLICIT_HOURS_CUES)

        if not cue:
            return {"days": [], "start": "", "end": ""}, ""

    days = []
    start = ""
    end = ""

    if "mon-fri" in t or ("monday" in t and "friday" in t):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    if "weekdays" in t and not days:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    m = re.search(
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
        t
    )

    evidence = ""

    if m:

        start = f"{m.group(1)}{m.group(3)}"
        end = f"{m.group(4)}{m.group(6)}"

        evidence = _snippet(text, m.start(0))

    return {"days": days, "start": start, "end": end}, evidence


def extract_integration_constraints(text, strict=True):

    t = text.lower()

    constraints = []
    evidence = {}

    if strict:

        cue = _find_evidence(text, EXPLICIT_CONSTRAINT_CUES)

        if not cue:
            return [], {}

    patterns = [
        "never create sprinkler jobs in servicetrade",
        "do not create sprinkler jobs in servicetrade",
        "never create jobs in servicetrade"
    ]

    for p in patterns:

        idx = t.find(p)

        if idx != -1:
            constraints.append(p)
            evidence[p] = _snippet(text, idx)

    return constraints, evidence


# ----------------------------
# Main builder
# ----------------------------

def build_memo(account_id: str, text: str, stage: str):

    strict = (stage == "demo")

    company_name, ev_company = extract_company_name(text)
    timezone, ev_tz = extract_timezone(text)

    business_hours, ev_hours = extract_business_hours(text, strict)
    business_hours["timezone"] = timezone

    services_supported, ev_services = extract_services(text, strict)

    emergency_definition, ev_emerg = extract_emergencies(text, strict)

    phones, ev_phones = extract_phones(text)

    integration_constraints, ev_constraints = extract_integration_constraints(text, strict)

    routing_cue = _find_evidence(text, EXPLICIT_ROUTING_CUES)

    routing_contacts = phones if routing_cue else []

    # ----------------------------
    # Questions for missing fields
    # ----------------------------

    questions = []

    if not company_name:
        questions.append("Need company_name")

    if not business_hours["days"] or not business_hours["start"] or not business_hours["end"]:
        questions.append("Need business_hours (days/start/end)")

    if not timezone:
        questions.append("Need timezone")

    if not emergency_definition:
        questions.append("Need emergency_definition")

    if not services_supported:
        questions.append("Need services_supported")

    if not routing_contacts:
        questions.append("Need routing phone numbers and routing rules (who to call for emergencies / non-emergencies)")

    # ----------------------------
    # Confidence scoring
    # ----------------------------

    def confidence(val):

        if not val:
            return "missing"

        if stage == "demo":
            return "medium"

        return "high"

    confidence_map = {

        "company_name": confidence(company_name),
        "timezone": confidence(timezone),
        "business_hours": confidence(business_hours["days"]),
        "services_supported": confidence(services_supported),
        "emergency_definition": confidence(emergency_definition),
        "routing_rules": confidence(routing_contacts),
        "integration_constraints": confidence(integration_constraints)
    }

    # ----------------------------
    # Evidence
    # ----------------------------

    evidence = {

        "company_name": ev_company,
        "timezone": ev_tz,
        "business_hours": ev_hours,
        "services_supported": ev_services,
        "emergency_definition": ev_emerg,
        "phones": ev_phones,
        "integration_constraints": ev_constraints,
        "routing_cue": routing_cue
    }

    # ----------------------------
    # Memo object
    # ----------------------------

    memo = {

        "account_id": account_id,

        "company_name": company_name,

        "business_hours": business_hours,

        "office_address": "",

        "services_supported": services_supported,

        "emergency_definition": emergency_definition,

        "emergency_routing_rules": {
            "contacts": routing_contacts,
            "order": routing_contacts,
            "fallback": ""
        },

        "non_emergency_routing_rules": {
            "contacts": routing_contacts,
            "order": routing_contacts,
            "fallback": ""
        },

        "call_transfer_rules": {
            "timeout_seconds": 25,
            "retries": 1,
            "fail_message": ""
        },

        "integration_constraints": integration_constraints,

        "after_hours_flow_summary": "",
        "office_hours_flow_summary": "",

        "questions_or_unknowns": questions,

        "notes": "Strict extraction. Missing fields are explicitly flagged.",

        "_meta": {

            "stage": stage,

            "confidence": confidence_map,

            "evidence": evidence
        }
    }

    return memo