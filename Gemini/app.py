import os
from fastapi import FastAPI

app = FastAPI(title="K8s-GitOps-Demo")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "engine": "ArgoCD Pull Model",
        "message": "Hello from a secure GitOps workflow!"
    }

@app.get("/healthz")
def health_check():
    return {"status": "OK"}
