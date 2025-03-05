FROM python:3.11
ENV PYTHONUNBUFFERED=1
WORKDIR /chat-service-dockerized

# Upgrade pip and setuptools before installing dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /chat-service-dockerized/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . /chat-service-dockerized/

# Install curl
# RUN apt-get update && apt-get install -y curl
