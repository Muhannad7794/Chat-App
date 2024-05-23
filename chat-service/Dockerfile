FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /chat-service-dockerized

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /chat-service-dockerized/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . /chat-service-dockerized/

# Install curl
# RUN apt-get update && apt-get install -y curl
