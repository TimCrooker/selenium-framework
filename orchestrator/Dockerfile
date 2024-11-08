# orchestrator/Dockerfile

FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy orchestrator code
COPY . /app

# Set environment variables
ENV ORCHESTRATOR_URL=http://orchestrator:8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
