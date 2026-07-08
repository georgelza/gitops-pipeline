
To get from a bare Kubernetes cluster to a fully automated GitOps pipeline using a pull-based model, we must execute the configurations in a strict, linear progression.

Here is the complete, cohesive roadmap.

1. Directory Structure

Create this exact layout on your local workstation before creating the configuration files:

```
├── app.py                  # FastAPI source code
├── Dockerfile              # Docker compilation recipe
├── requirements.txt        # Python packages
├── argocd-app.yaml        # ArgoCD Application Definition manifest
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions pipeline blueprint
└── k8s/
    └── deployment.yaml    # Kubernetes manifests
```

2. Source Configuration Blueprints

app.py

```Python
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

```

requirements.txt

```
fastapi>=0.110.0
uvicorn>=0.28.0
```

Dockerfile

```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
USER 65534
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

k8s/deployment.yaml

(Replace YOUR_DOCKERHUB_USERNAME with your actual Docker Hub username)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app-deployment
  namespace: app
  labels:
    app: python-fastapi
spec:
  replicas: 2
  selector:
    matchLabels:
      app: python-fastapi
  template:
    metadata:
      labels:
        app: python-fastapi
    spec:
      containers:
      - name: fastapi-app
        image: georgelza/python-fastapi-app:1.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 5
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: python-app-service
  namespace: app
spec:
  selector:
    app: python-fastapi
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: NodePort
```

.github/workflows/ci.yml

```YAML
name: CI Build and Manifest Update

on:
  push:
    branches: [ main ]
    paths-ignore:
      - 'k8s/**'  # Prevents infinite build loops when updating YAMLs

jobs:
  build-and-patch:
    runs-on: ubuntu-latest  # Configures GitHub to provision the standard compilation runner
    permissions:
      contents: write       # Grants the runner authorization to commit changes back to Git

    steps:
    - name: Checkout Source Code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Build and Push Docker Image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:latest
          ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:${{ github.sha }}

    - name: Update Manifest Image Tag
      run: |
        # Replaces the text placeholder with the precise Git commit SHA
        sed -i -E "s|(image: ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:).*|\1${{ github.sha }}|" k8s/deployment.yaml
        
        # Commits the manifest alteration back to the repository
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
        git add k8s/deployment.yaml
        git commit -m "chore: auto-update image tag to ${{ github.sha }} [skip ci]"
        git push
```

argocd-app.yaml

(Replace YOUR_GITHUB_USERNAME and YOUR_REPO_NAME with your repo information)

```YAML
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-gitops-pipeline
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/georgelza/gitops-pipeline.git'
    targetRevision: main
    path: k8s
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: app  # Target workload namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

3. End-to-End Execution Checklist

### Phase 1: Cluster Bootstrap & ArgoCD Setup (On Cluster Control Plane)

Execute these commands on your bare-metal cluster terminal using your administrative privileges:

```Bash
# 1. Create the engine control plane namespace
kubectl create namespace argocd

# 2. Deploy stable ArgoCD infrastructure components
#kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd create -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Create your designated application workload namespace
kubectl create namespace app

# 4. Block and watch until all operators show "Running"
kubectl get pods -n argocd -w
```

(Press Ctrl+C to exit the watch block once all statuses show Running).

### Phase 2: Configure Authentication (On GitHub UI)

Go to your Docker Hub profile, click Account Settings -> Security -> Personal Access Tokens, and generate a new Read/Write token.
In your GitHub browser window, open your repository, click Settings -> Secrets and variables -> Actions -> New repository secret.
Create two secrets matching these keys exactly:

Name: DOCKERHUB_USERNAME | Value: Your Docker Hub user name
Name: DOCKERHUB_TOKEN | Value: The token string generated above

### Phase 3: Provision the Runner & Push Baseline (From Workstation)

Now, push your local folder setup to GitHub. This triggers the GitHub-hosted runner to provision its computing workspace, build the image, and output the tracking tag.

```Bash
git add .
git commit -m "ci: establish core framework baseline"
git push origin main
```

⏳ Pause Strategy: Open your GitHub repository web browser interface and click on the Actions tab. Wait until the active runner job executes completely and displays a green checkmark. If you inspect your k8s/deployment.yaml file in the GitHub UI, you will see that the text :placeholder has been updated to your long Git commit SHA string.

### Phase 4: Wire the Cluster to Pull Manifests (On Cluster Control Plane)

With the correct image tag committed back to your Git repository, instruct ArgoCD to monitor the repository and deploy the resources to your targeted namespace. Run this command on your cluster terminal:

```Bash
kubectl apply -f argocd-app.yaml
```

ArgoCD instantly reads the k8s/deployment.yaml file from your repository, translates the requirements, handles the target definitions, and sets up your application inside the app namespace.

4. Verification

Verify that your application has been safely pulled and initiated within its designated workspace:

```Bash
kubectl get deployments,services,pods -n app -o wide
```

5. Future Redeploy Action-Trigger Loop

For every future code alteration or deployment update, you do not need to repeat any of the steps above. The automated loops trigger natively when a commit lands:

You push an update to app.py from your local workspace:

```Bash
git add app.py
git commit -m "feat: upgrade runtime message block"
git push origin main
```

GitHub Runner Compiles: The GitHub Actions workflow detects the code changes, builds a fresh image tagged with the new Git commit SHA, and pushes it to Docker Hub.

GitHub Runner Patches Git: The runner overwrites the image: tag inside k8s/deployment.yaml with the new Git SHA and commits it back to the repository.

ArgoCD Detects and Pulls: ArgoCD notices the updated manifest in Git, pulls down the new declaration, and coordinates a safe, zero-downtime rolling deployment upgrade within your cluster's app namespace.