FROM python:3.11
ENV PYTHONUNBUFFERED=1
WORKDIR /users-management-service-dockerized

# Install required system dependencies for Pillow and other compiled packages
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev build-essential \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libtiff-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools before installing dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /users-management-service-dockerized/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . /users-management-service-dockerized/

# Install curl
# RUN apt-get update && apt-get install -y curl
