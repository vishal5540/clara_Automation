def diff_dict(old, new, path=""):
    changes = []

    if isinstance(old, dict) and isinstance(new, dict):
        keys = set(old.keys()) | set(new.keys())
        for k in sorted(keys):
            if k == "_meta":
                continue
            changes += diff_dict(old.get(k), new.get(k), path + "/" + k)
        return changes

    if isinstance(old, list) and isinstance(new, list):
        if old != new:
            changes.append({
                "path": path,
                "from": old,
                "to": new,
                "reason": "Onboarding update"
            })
        return changes

    if old != new:
        changes.append({
            "path": path,
            "from": old,
            "to": new,
            "reason": "Onboarding update"
        })

    return changes


def changes_md(changes, conflicts):
    lines = ["# Changes (v1 → v2)\n"]

    if conflicts:
        lines.append("## Conflicts (Onboarding overrides demo)\n")
        for c in conflicts:
            lines.append(f"- **{c['path']}**: `{c['from']}` → `{c['to']}` ({c['reason']})")
        lines.append("")

    lines.append("## Applied Changes\n")
    if not changes:
        lines.append("- No changes detected.\n")
    else:
        for c in changes:
            lines.append(f"- **{c['path']}**: `{c['from']}` → `{c['to']}` ({c['reason']})")
        lines.append("")

    return "\n".join(lines)