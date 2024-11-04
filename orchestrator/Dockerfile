FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies from orchestrator/requirements.txt
COPY orchestrator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the orchestrator code
COPY orchestrator /app/orchestrator

EXPOSE 8000

CMD ["uvicorn", "orchestrator.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
