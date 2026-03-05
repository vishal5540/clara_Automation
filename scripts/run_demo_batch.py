import os, glob, json
from scripts.utils import read_text, write_json, write_text, now_iso, deterministic_account_id, sha1_text
from scripts.extract_memo import build_memo
from scripts.generate_agent_spec import render_agent_spec

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run():
    demo_dir = os.path.join(BASE, "inputs", "demo")
    out_root = os.path.join(BASE, "outputs", "accounts")
    templates_dir = os.path.join(BASE, "templates")

    for path in sorted(glob.glob(os.path.join(demo_dir, "*.*"))):
        filename = os.path.basename(path)
        account_id = deterministic_account_id(filename)
        text = read_text(path)
        input_hash = sha1_text(text)

        v1_dir = os.path.join(out_root, account_id, "v1")
        meta_path = os.path.join(v1_dir, "meta.json")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("input_hash") == input_hash:
                print(f"SKIP (unchanged): {filename}")
                continue

        memo = build_memo(account_id, text, stage="demo")
        agent_yaml = render_agent_spec(memo, "v1", templates_dir)

        write_json(os.path.join(v1_dir, "memo.json"), memo)
        write_text(os.path.join(v1_dir, "agent_spec.yaml"), agent_yaml)
        write_json(meta_path, {
            "source_file": filename,
            "generated_at": now_iso(),
            "version": "v1",
            "stage": "demo",
            "input_hash": input_hash
        })

        print(f"OK: {filename} -> {account_id}/v1")

    print("Demo batch complete.")

if __name__ == "__main__":
    run()