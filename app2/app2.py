
from fastapi import FastAPI

app = FastAPI(title="K8s-GitOps-App2-Helper")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "component": "App 2 Helper Sub-System",
        "message": "Hello! I am running on port 9000 in my own namespace."
    }

@app.get("/healthz")
def health_check():
    return {"status": "OK"}