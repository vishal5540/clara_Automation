import copy

ALLOWED_UPDATE_TOP_LEVEL = {
    "company_name",
    "business_hours",
    "office_address",
    "services_supported",
    "emergency_definition",
    "emergency_routing_rules",
    "non_emergency_routing_rules",
    "call_transfer_rules",
    "integration_constraints",
}

def _is_blank(v):
    return v in ("", None, [], {})

def merge_memo_v1_to_v2(v1: dict, patch: dict):
    """
    v1 = demo memo
    patch = onboarding memo (stage=onboarding)
    Return: (v2, conflicts, applied)
    """
    v2 = copy.deepcopy(v1)
    conflicts = []
    applied = []

    patch_status = (patch.get("_meta", {}) or {}).get("fields_status", {})

    def apply_field(key):
        nonlocal v2
        if key not in patch:
            return

        # Only update if patch has something non-blank and it was explicit (or at least not missing)
        status = patch_status.get(key, "missing")
        if status == "missing":
            return

        new_val = patch.get(key)
        if _is_blank(new_val):
            return

        old_val = v2.get(key)

        # merge rules:
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            # deep merge dict but do not overwrite with blanks
            merged = copy.deepcopy(old_val)
            for k, v in new_val.items():
                if _is_blank(v):
                    continue
                merged[k] = v
            if merged != old_val:
                if old_val and old_val != merged:
                    conflicts.append({
                        "path": f"/{key}",
                        "from": old_val,
                        "to": merged,
                        "reason": "Onboarding confirmed/overrode demo value"
                    })
                v2[key] = merged
                applied.append(f"/{key}")
            return

        if isinstance(old_val, list) and isinstance(new_val, list):
            # For lists, onboarding extends but can also override if clearly different.
            merged = []
            for item in new_val:
                if item not in merged:
                    merged.append(item)
            if merged != old_val and merged:
                if old_val and old_val != merged:
                    conflicts.append({
                        "path": f"/{key}",
                        "from": old_val,
                        "to": merged,
                        "reason": "Onboarding confirmed/overrode demo list"
                    })
                v2[key] = merged
                applied.append(f"/{key}")
            return

        # primitives
        if old_val != new_val:
            if not _is_blank(old_val):
                conflicts.append({
                    "path": f"/{key}",
                    "from": old_val,
                    "to": new_val,
                    "reason": "Onboarding confirmed/overrode demo value"
                })
            v2[key] = new_val
            applied.append(f"/{key}")

    for k in sorted(ALLOWED_UPDATE_TOP_LEVEL):
        apply_field(k)

    # Update meta stage
    v2["_meta"] = v2.get("_meta", {}) or {}
    v2["_meta"]["stage"] = "v2"
    v2["_meta"]["merged_from"] = "demo(v1)+onboarding(patch)"
    v2["_meta"]["applied_paths"] = applied

    # Recompute questions: remove ones now satisfied
    q = []
    bh = v2.get("business_hours", {}) or {}
    if not v2.get("company_name"):
        q.append("Need company_name")
    if not (bh.get("days") and bh.get("start") and bh.get("end")):
        q.append("Need business_hours (days/start/end)")
    if not bh.get("timezone"):
        q.append("Need timezone")
    if not v2.get("emergency_definition"):
        q.append("Need emergency_definition")
    if not v2.get("services_supported"):
        q.append("Need services_supported")

    rr = v2.get("emergency_routing_rules", {}) or {}
    if not rr.get("contacts"):
        q.append("Need routing phone numbers and routing rules (who to call for emergencies / non-emergencies)")

    v2["questions_or_unknowns"] = q
    return v2, conflicts, applied