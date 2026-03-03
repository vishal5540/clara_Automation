import copy

def merge_memo(base: dict, patch: dict) -> dict:
    result = copy.deepcopy(base)

    def merge(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            for k, v in b.items():
                if k not in a:
                    a[k] = v
                else:
                    a[k] = merge(a[k], v)
            return a

        if isinstance(a, list) and isinstance(b, list):
            merged = []
            for item in a + b:
                if item not in merged:
                    merged.append(item)
            return merged

        if b in ("", None, [], {}):
            return a

        return b

    result = merge(result, patch)

    # Clean resolved unknowns
    questions = result.get("questions_or_unknowns", [])
    cleaned = []
    for q in questions:
        if q == "Need company_name" and result.get("company_name"):
            continue
        cleaned.append(q)

    result["questions_or_unknowns"] = cleaned
    return result