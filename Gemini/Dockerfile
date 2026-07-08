FROM python:3.11-slim
WORKDIR /app

# Install dependencies early to leverage Docker layer caching

COPY requirements.txt .

# Disable pip cache to keep the container footprint small
# --no-cache-dir reduces final image size significantly
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Expose the app port
EXPOSE 8000

# Run as a non-privileged user for enhanced K8s security

USER 65534

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]