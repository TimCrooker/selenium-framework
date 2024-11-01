FROM selenium/standalone-chrome:latest

USER root

# Install Python and necessary packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir pymongo python-socketio[client]

WORKDIR /app

# Copy dependencies for the bots
COPY bots/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy bot scripts and framework code
COPY bots /app/bots
COPY framework /app/framework

CMD ["python3"]
