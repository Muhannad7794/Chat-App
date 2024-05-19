FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /users_management_service_dockerized

# Copy the current directory contents into the container
COPY . /users_management_service_dockerized/

# Install curl
RUN apt-get update && apt-get install -y curl

# Install dependencies
COPY requirements.txt /users_management_service_dockerized/
RUN pip install -r requirements.txt

