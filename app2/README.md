
## Bosses Scope creep, our app2.

So we now have this new requirement, it's a piece of extra code, that will result in a new container.

Below is the code, as per the files in <project_root>/app2 followed by the steps required to have this form part of our ArgoCD / Github Actions pipeline.


## New Artifacts

--app2.py

```python

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
```

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn
COPY app2.py .
EXPOSE 9000
USER 65534
CMD ["uvicorn", "app2:app", "--host", "0.0.0.0", "--port", "9000"]
```

--new deployment.yml
Step 1: To deploy we will copy/replace the current k8s/deployment.yml

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
        image: georgelza/python-fastapi-app:c7770605464afad40e9d4fa8736768736d8beb90
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

---
apiVersion: v1
kind: Namespace
metadata:
  name: app2-space
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app2-deployment
  namespace: app2-space
  labels:
    app: python-fastapi-two
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-fastapi-two
  template:
    metadata:
      labels:
        app: python-fastapi-two
    spec:
      containers:
      - name: fastapi-app2
        # The runner will dynamically patch this placeholder just like App 1
        image: georgelza/python-fastapi-app2:placeholder
        imagePullPolicy: Always
        ports:
        - containerPort: 9000
        livenessProbe:
          httpGet:
            path: /healthz
            port: 9000
          initialDelaySeconds: 5
        readinessProbe:
          httpGet:
            path: /healthz
            port: 9000
          initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: python-app2-service
  namespace: app2-space
spec:
  selector:
    app: python-fastapi-two
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9000
  type: NodePort
```

--new .github/workflows/ci.yml

Step 2: To deploy we will copy/replace the current .github/workflows/ci.yml

```yaml
name: CI Build and Manifest Update

on:
  push:
    branches:
      - main
    paths-ignore:
      - 'k8s/**'

jobs:
  build-and-patch:
    runs-on: ubuntu-latest
    permissions:
      contents: write

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

    # BUILD APP 1 (Untouched)
    - name: Build and Push App 1
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile
        push: true
        platforms: linux/amd64,linux/arm64
        tags: |
          ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:latest
          ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    # BUILD APP 2 (Addition)
    - name: Build and Push App 2
      uses: docker/build-push-action@v5
      with:
        context: ./app2
        file: ./app2/Dockerfile
        push: true
        platforms: linux/amd64,linux/arm64
        tags: |
          ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app2:latest
          ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app2:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    # PATCH BOTH MANIFEST TAGS
    - name: Update Manifest Image Tags
      run: |
        # Patches both app images inside the same k8s/deployment.yml file
        sed -i -E "s|(image: ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app:).*|\1${{ github.sha }}|" k8s/deployment.yml
        sed -i -E "s|(image: ${{ secrets.DOCKERHUB_USERNAME }}/python-fastapi-app2:).*|\1${{ github.sha }}|" k8s/deployment.yml
        
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
        
        git add k8s/deployment.yml
        git commit -m "chore: auto-update image tags for app1 and app2 to ${{ github.sha }} [skip ci]"
        git push
```

Step 3: Execution (The Git Loop)

Since ArgoCD is already tracking your k8s/ folder via your existing application setup, you don't even need to register a new file with ArgoCD! The moment you commit these additions, ArgoCD will notice the appended blocks at the bottom of the manifest and natively deploy them.

Execute your commands locally:

```bash
# 1. Bring down the tracking tag changes from the last run
git pull origin main

# 2. Stage the new app2 folder and file updates
git add .

# 3. Commit the structural expansion non-invasively
git commit -m "feat: non-invasively introduce app2 helper sub-system"

# 4. Push to production
git push origin main
```

Once the pipeline goes green, verify both components are happily coexisting in your cluster under their own namespaces:

```bash
kubectl get pods -n app
kubectl get pods -n app2-space
```

Step 4: Verify

We can now configure a new port-forward as per previous to reach our application

```bash
kubectl port-forward svc/python-app2-deployment -n app2-space 9080:80
```

In a new terminal

```bash
curl -i http://localhost:9080/

HTTP/1.1 200 OK
date: Wed, 08 Jul 2026 15:03:44 GMT
server: uvicorn
content-length: 98
content-type: application/json

{"status": "healthy", "component": "App 2 Helper Sub-System", "message": "Hello! I am running on port 9000 in my own namespace."}
```

You can also navigate with you browser to go to:

- http://localhost:9080/ or 
- http://localhost:9080/healthz or similarly to 
- http://127.0.0.1:9080/
- http://127.0.0.1:9080/health