FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /chat_service_dockerized

# Copy the current directory contents into the container
COPY . /chat_service_dockerized/

# Install dependencies
COPY requirements.txt /chat_service_dockerized/
RUN pip install -r requirements.txt

