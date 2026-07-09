## Project structure

Short layout of all the files that make up our project/article.

```
.
├── .github/
│   └── workflows/
│       └── ci.yml          # CI Pipeline (Builds image, updates manifest)
├── blog-doc/
│   └── diagrams/
├── k8s/
│   └── deployment.yml      # Kubernetes manifests (Deployment & Service)
├── my-pipeline             # diagrams and screenshots
├── .gitignore
├── app.py                  # FastAPI Application source code
├── argocd-app.yml          # Docker recipe
├── BUILD.md                # Docker recipe
├── Dockerfile              # Docker recipe
├── README.md               # Docker recipe
├── requirements.txt        # Python dependencies
├── structure.md            # This file
└── vcluster.yml            # 
```