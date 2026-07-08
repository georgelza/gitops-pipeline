
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

- app.py

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

```bash
python3 -m venv ./venv

source venv/bin/activate

pip install --upgrade pip

pip install -r requirements
```

--requirements

```bash
fastapi>=0.110.0
uvicorn>=0.28.0
```

--Dockerfile

```bash
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
USER 65534
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

--k8s/deployment.yaml

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
        image: georgelza/python-fastapi-app:placeholder
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

--.github/workflows/ci.yml

```YAML
name: CI Build and Manifest Update

on:
  push:
    branches:
      - main
    paths-ignore:
      - 'deployment.yml' # <-- Updated from 'k8s/**'

jobs:
  build-and-patch:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Allows pushing the updated YAML tag back to Git

    steps:
    - name: Checkout Source Code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Fetches full history for proper Git tracking

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
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Update Manifest Image Tag
      run: |
        # 1. Target the file inside your k8s/ folder matching your exact .yml extension
        sed -i -E "s|(image: ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:).*|\1${{ github.sha }}|" k8s/deployment.yml
        
        # 2. Configure a Git Identity
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
        
        # 3. Track and commit the exact file from the k8s directory path
        git add k8s/deployment.yml
        git commit -m "chore: auto-update deployment image tag to ${{ github.sha }} [skip ci]"
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

Go to your Docker Hub profile, click Account Settings -> Security -> Personal Access Tokens, and generate a new **Read/Write** token.

Now that you have generated that personal access token (the key) from Docker Hub, you need to save it inside GitHub.

Think of GitHub as the builder that needs keys to enter your warehouse (Docker Hub). If you paste these keys directly into your code, anyone who looks at your repository can steal them. Instead, you put them into GitHub's secure vault called Actions Secrets.

Here is exactly what you do, step-by-step, inside your web browser.

- Step 0: Register/Create new repository, for our blog we're using *gitops-pipeline*

- Step 1: Open Your Repository's Vault

  - Open your web browser and go to GitHub.

  - Navigate to your specific code repository for this project.

  - Look at the horizontal menu tabs near the top (Code, Issues, Pull Requests...). Click on the Settings tab (it has a gear icon ⚙️).

- Step 2: Navigate to Actions Secrets

  - On the left-hand sidebar, scroll down until you see the *Security and quality*.
  
  - Click on *secrets and variables* and variables to expand it, then click on Actions.

You are now in the secure vault workspace.

- Step 3: Add Your Docker Hub Username

  - Click the green button at the Right/middle that says *New repository secret*.
  
  - In the Name field, type exactly this:  DOCKERHUB_USERNAME

  - In the Secret field, type your actual Docker Hub username (the name you use to log into hub.docker.com).

  - Click the green Add secret button.

- Step 4: Add Your Docker Hub Key (The Token)

  - Click that green *New repository secret* button one more time.

  - In the Name field, type exactly this: DOCKERHUB_TOKEN

  - In the Secret field, paste the complete personal access token string you copied from Docker Hub.

  - Click the green Add secret button.


What Did We Just Accomplish?

By doing this, you have securely wired the two platforms together without hardcoding sensitive details.

When you push your code, the GitHub-hosted runner spins up and runs the automated blueprint file (*.github/workflows/ci.yml*). When it reaches these lines:

```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

The runner automatically reaches into the secure vault, grabs your username and token on the fly, logs into Docker Hub, pushes your compiled Python container, and vanishes—keeping your credentials entirely secure.

Now that these secrets are saved, you are ready to commit and push your files from your local workstation to trigger the initial container build.


### Phase 3: Provision the Runner & Push Baseline (From Workstation)

Now, push your local folder setup to GitHub. This triggers the GitHub-hosted runner to provision its computing workspace, build the image, and output the tracking tag.

```Bash
git add .
git commit -m "ci: establish core framework baseline"
git push origin main
```

⏳ Pause Strategy: Open your GitHub repository web browser interface and click on the Actions tab. Wait until the active runner job executes completely and displays a green checkmark. If you inspect your *k8s/deployment.yaml* file in the GitHub UI, you will see that the text :placeholder has been updated to your long Git commit SHA string.

### Phase 4: Wire the Cluster to Pull Manifests (On Cluster Control Plane)

With the correct image tag committed back to your Git repository, instruct ArgoCD to monitor the repository and deploy the resources to your targeted namespace. Run this command on your cluster terminal:

```Bash
kubectl apply -f argocd-app.yaml
```

ArgoCD instantly reads the *k8s/deployment.yaml* file from your repository, translates the requirements, handles the target definitions, and sets up your application inside the app namespace.

4. Verification

Verify that your application has been safely pulled and initiated within its designated workspace:

```Bash
kubectl get deployments,services,pods -n app -o wide
```

```
NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS    IMAGES                                                                  SELECTOR
deployment.apps/python-app-deployment   2/2     2            2           30m   fastapi-app   georgelza/python-fastapi-app:b89529def5d346c70f7ef773551cee670ce54e5c   app=python-fastapi

NAME                         TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/python-app-service   NodePort   10.99.36.33   <none>        80:30449/TCP   30m   app=python-fastapi

NAME                                        READY   STATUS    RESTARTS   AGE   IP           NODE       NOMINATED NODE   READINESS GATES
pod/python-app-deployment-8c9cf4c48-8h8s8   1/1     Running   0          19m   10.244.3.4   worker-2   <none>           <none>
pod/python-app-deployment-8c9cf4c48-r8krk   1/1     Running   0          20m   10.244.4.4   worker-3   <none>           <none>
```

5. Future Redeploy Action-Trigger Loop

For every future code alteration or deployment update, you do not need to repeat any of the steps above. The automated loops trigger natively when a commit lands:

You push an update to *app.py* from your local workspace:

```Bash
git add app.py
git commit -m "feat: upgrade runtime message block"
git push origin main
```

To access your newly deployed FastAPI application from your workstation, you have two clear options based on your NodePort configuration.

- Option 1: Access via NodePort (Direct Cluster Routing)

Your python-app-service manifest correctly configured a NodePort service. Looking at your kubectl get output:

```bash
service/python-app-service   NodePort   10.99.36.33   <none>   80:30449/TCP
```

Kubernetes has opened port 30449 across every single physical node in your cluster.

To access the app directly, find the host IP address of any of your cluster nodes (such as the machine hosting worker-2 or worker-3) and navigate to it in your browser on that high port:

```bash
http://<ANY_CLUSTER_NODE_IP>:30449/
```

- Option 2: Use a kubectl Port-Forward Tunnel (Recommended for Testing)

If you want to map the cluster application specifically to your workstation's localhost:8000 interface for convenient local testing, you can instruct kubectl to open a secure, bidirectional network tunnel from your desktop straight to the service.

Run this command in a separate terminal window on your workstation:

```bash
kubectl port-forward svc/python-app-service -n app 8080:80
```

What this does:

This binds your workstation's local port 8000 directly to the cluster service's incoming port 80.
Once that command is running, open your web browser and navigate to:

NOW, you may ask, but our app is exposed on port 8000 in the container, see the *Dockefile*, should we not be using this port?

Our configuration is actually completely correct as it stands, and you do not need to change the application's internal container port (8000).

In your Kubernetes manifest, you created a translation layer using the Service definition. Let's look at how the traffic flows:

```yaml
ports:
    - protocol: TCP
      port: 80         # <-- The Service's entry port inside the cluster
      targetPort: 8000 # <-- The port the Service forwards to inside the container
```
Because of this mapping, the Service listens on port 80 inside the cluster network and automatically shifts the traffic to port 8000 inside your Python container.

**Why Option 2** (kubectl port-forward) works with your setup:

When you run a port-forward command, you specify LOCAL_PORT:CLUSTER_SERVICE_PORT. Since your service is listening on port 80, your command should target port 80 like this:

```bash
kubectl port-forward svc/python-app-service -n app 8080:80
```

In a new terminal

```bash
curl -i http://localhost:8080/

HTTP/1.1 200 OK
date: Wed, 08 Jul 2026 15:03:44 GMT
server: uvicorn
content-length: 98
content-type: application/json

{"status":"healthy","engine":"ArgoCD Pull Model","message":"Hello from a secure GitOps workflow!"}
```

You can also navigate with you browser to go to 
- http://localhost:8080/ or 
- http://localhost:8080/healthz or similarly to 
- 127.0.0.1:8080/
- 127.0.0.1:8080/health


GitHub Runner Compiles: The GitHub Actions workflow detects the code changes, builds a fresh image tagged with the new Git commit SHA, and pushes it to Docker Hub.

GitHub Runner Patches Git: The runner overwrites the image: tag inside k8s/deployment.yaml with the new Git SHA and commits it back to the repository.

ArgoCD Detects and Pulls: ArgoCD notices the updated manifest in Git, pulls down the new declaration, and coordinates a safe, zero-downtime rolling deployment upgrade within your cluster's app namespace.