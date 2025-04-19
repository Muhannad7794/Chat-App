FROM python:3.11
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=translation_manager.settings

WORKDIR /translation-service-dockerized

# Install system deps
RUN apt-get update && apt-get install -y netcat-openbsd

# Upgrade pip and setuptools before installing dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /translation-service-dockerized/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the code
COPY . /translation-service-dockerized/