FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY protos/ ./protos/
COPY services/data_ingestion/ ./

RUN apt-get update && \
    apt-get install -y protobuf-compiler && \
    pip install --no-cache-dir -r requirements.txt && \
    protoc -I=protos --python_out=. protos/*.proto

CMD ["python", "main.py"]