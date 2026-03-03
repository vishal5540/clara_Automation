import os, glob
from scripts.utils import read_text, write_json, write_text, now_iso, deterministic_account_id
from scripts.extract_memo import build_memo
from scripts.generate_agent_spec import render_agent_spec

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run():
    demo_dir = os.path.join(BASE, "inputs", "demos")
    out_root = os.path.join(BASE, "outputs", "accounts")
    templates_dir = os.path.join(BASE, "templates")

    for path in sorted(glob.glob(os.path.join(demo_dir, "*.*"))):
        filename = os.path.basename(path)
        account_id = deterministic_account_id(filename)
        text = read_text(path)

        memo = build_memo(account_id, text)
        agent_yaml = render_agent_spec(memo, "v1", templates_dir)

        v1_dir = os.path.join(out_root, account_id, "v1")

        write_json(os.path.join(v1_dir, "memo.json"), memo)
        write_text(os.path.join(v1_dir, "agent_spec.yaml"), agent_yaml)
        write_json(os.path.join(v1_dir, "meta.json"), {
            "source_file": filename,
            "generated_at": now_iso(),
            "version": "v1"
        })

    print("Demo batch complete.")

if __name__ == "__main__":
    run()