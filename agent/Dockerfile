# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y gcc libffi-dev make

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chrome browser and Chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium-driver \
    chromium

# Add Selenium-specific paths if needed
ENV PATH="/usr/lib/chromium-browser/:${PATH}"

# Copy agent code
COPY . /app

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose the Agent API Port
EXPOSE 9000

# Command to run the agent
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
