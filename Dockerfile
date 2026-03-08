FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install python deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app code
COPY . .

# create dirs for persistent storage
RUN mkdir -p chroma_db

# expose both ports
EXPOSE 8000
EXPOSE 8501

# startup script runs both uvicorn and streamlit
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]