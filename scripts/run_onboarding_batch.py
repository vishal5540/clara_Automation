import os, glob, json
from scripts.utils import read_text, write_json, write_text, now_iso, deterministic_account_id
from scripts.extract_memo import build_memo
from scripts.generate_agent_spec import render_agent_spec
from scripts.merge_patch import merge_memo
from scripts.diff_and_changelog import diff_dict, changes_md

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run():
    onboarding_dir = os.path.join(BASE, "inputs", "onboarding")
    out_root = os.path.join(BASE, "outputs", "accounts")
    templates_dir = os.path.join(BASE, "templates")

    for path in sorted(glob.glob(os.path.join(onboarding_dir, "*.*"))):
        filename = os.path.basename(path)
        account_id = deterministic_account_id(filename)

        v1_path = os.path.join(out_root, account_id, "v1", "memo.json")
        if not os.path.exists(v1_path):
            print(f"Skipping {filename}: v1 not found.")
            continue

        with open(v1_path, "r", encoding="utf-8") as f:
            v1 = json.load(f)

        onboarding_text = read_text(path)
        patch = build_memo(account_id, onboarding_text)

        v2 = merge_memo(v1, patch)
        agent_yaml = render_agent_spec(v2, "v2", templates_dir)

        v2_dir = os.path.join(out_root, account_id, "v2")
        write_json(os.path.join(v2_dir, "memo.json"), v2)
        write_text(os.path.join(v2_dir, "agent_spec.yaml"), agent_yaml)
        write_json(os.path.join(v2_dir, "meta.json"), {
            "source_file": filename,
            "generated_at": now_iso(),
            "version": "v2"
        })

        changes = diff_dict(v1, v2)
        changelog_dir = os.path.join(out_root, account_id, "changelog")

        write_json(os.path.join(changelog_dir, "changes.json"), changes)
        write_text(os.path.join(changelog_dir, "changes.md"), changes_md(changes))

    print("Onboarding batch complete.")

if __name__ == "__main__":
    run()