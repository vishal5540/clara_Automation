from fastapi import FastAPI
import subprocess

app = FastAPI()

def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }

@app.post("/run-demo")
def run_demo():
    return _run(["python", "-m", "scripts.run_demo_batch"])

@app.post("/run-onboarding")
def run_onboarding():
    return _run(["python", "-m", "scripts.run_onboarding_batch"])