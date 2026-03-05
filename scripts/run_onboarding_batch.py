import os
import glob
import json

from scripts.utils import (
    read_text,
    write_json,
    write_text,
    now_iso,
    sha1_text
)

from scripts.extract_memo import build_memo
from scripts.generate_agent_spec import render_agent_spec
from scripts.merge_patch import merge_memo_v1_to_v2
from scripts.diff_and_changelog import diff_dict, changes_md


BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run():
    onboarding_dir = os.path.join(BASE, "inputs", "onboarding")
    out_root = os.path.join(BASE, "outputs", "accounts")
    templates_dir = os.path.join(BASE, "templates")

    for path in sorted(glob.glob(os.path.join(onboarding_dir, "*.*"))):

        filename = os.path.basename(path)

        # ------------------------------
        # FIX: extract account_id directly
        # ------------------------------
        if "_onboarding" in filename:
            account_id = filename.split("_onboarding")[0]
        else:
            print(f"SKIP (invalid filename): {filename}")
            continue

        v1_path = os.path.join(out_root, account_id, "v1", "memo.json")

        if not os.path.exists(v1_path):
            print(f"SKIP (no v1): {filename}")
            continue

        with open(v1_path, "r", encoding="utf-8") as f:
            v1 = json.load(f)

        onboarding_text = read_text(path)
        input_hash = sha1_text(onboarding_text)

        v2_dir = os.path.join(out_root, account_id, "v2")
        os.makedirs(v2_dir, exist_ok=True)

        meta_path = os.path.join(v2_dir, "meta.json")

        # Skip if unchanged
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            if meta.get("input_hash") == input_hash:
                print(f"SKIP (unchanged): {filename}")
                continue

        # Build onboarding memo patch
        patch = build_memo(account_id, onboarding_text, stage="onboarding")

        # Merge v1 → v2
        v2, conflicts, applied = merge_memo_v1_to_v2(v1, patch)

        # Generate agent spec
        agent_yaml = render_agent_spec(v2, "v2", templates_dir)

        # Write outputs
        write_json(os.path.join(v2_dir, "memo.json"), v2)
        write_text(os.path.join(v2_dir, "agent_spec.yaml"), agent_yaml)

        write_json(meta_path, {
            "source_file": filename,
            "generated_at": now_iso(),
            "version": "v2",
            "stage": "onboarding",
            "input_hash": input_hash,
            "applied_paths": applied,
            "conflict_count": len(conflicts)
        })

        # Generate changelog
        changes = diff_dict(v1, v2)

        changelog_dir = os.path.join(out_root, account_id, "changelog")
        os.makedirs(changelog_dir, exist_ok=True)

        write_json(os.path.join(changelog_dir, "changes.json"), {
            "conflicts": conflicts,
            "changes": changes
        })

        write_text(os.path.join(changelog_dir, "changes.md"),
                   changes_md(changes, conflicts))

        print(f"OK: {filename} -> {account_id}/v2 (+changelog)")

    print("Onboarding batch complete.")


if __name__ == "__main__":
    run()