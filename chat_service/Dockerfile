FROM python:3.11.4
ENV PYTHONUNBUFFERED=1
WORKDIR /chat_service_dockerized

# Copy the current directory contents into the container
COPY . /chat_service_dockerized/

# Install curl
RUN apt-get update && apt-get install -y curl

# Install dependencies
COPY requirements.txt /chat_service_dockerized/
RUN pip install --no-cache-dir -r requirements.txt
