# bots/Dockerfile

FROM python:3.9-slim

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium-driver \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY bots/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy bot scripts and framework code
COPY bots /app/bots

WORKDIR /app

# Set the entrypoint to a script that runs the specified bot
ENTRYPOINT ["python3", "/app/entrypoint.py"]
