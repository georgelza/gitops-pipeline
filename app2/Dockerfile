FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn
COPY app2.py .
EXPOSE 9000
USER 65534
CMD ["uvicorn", "app2:app", "--host", "0.0.0.0", "--port", "9000"]