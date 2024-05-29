FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /translation-service-dockerized

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /translation-service-dockerized/
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the code
COPY . /translation-service-dockerized/