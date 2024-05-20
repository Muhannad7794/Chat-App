FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /users-management-service-dockerized

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /users-management-service-dockerized/
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the code
COPY . /users-management-service-dockerized/

# Install curl
# RUN apt-get update && apt-get install -y curl
