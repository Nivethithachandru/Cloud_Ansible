FROM python:3.9-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV MEDIA_BASE_PATH=/app/

WORKDIR /app

COPY . /app
COPY .env /app/.env 

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    python3-distutils \ 
    && rm -rf /var/lib/apt/lists/


RUN python -m pip install --upgrade pip setuptools

RUN pip install -r requirements.txt
RUN pip install "uvicorn[standard]" websockets
RUN pip install uvicorn fastapi_utilities opencv-python Pillow psutil

EXPOSE 8016

CMD ["python3", "main.py", "runserver", "0.0.0.0:8016"]
