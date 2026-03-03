from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/run-demo")
def run_demo():
    result = subprocess.run(
        ["python", "-m", "scripts.run_demo_batch"],
        capture_output=True,
        text=True
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr
    }

@app.post("/run-onboarding")
def run_onboarding():
    result = subprocess.run(
        ["python", "-m", "scripts.run_onboarding_batch"],
        capture_output=True,
        text=True
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr
    }