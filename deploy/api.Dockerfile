FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home ops
COPY app app
COPY etl etl
COPY data/synthetic/pedidos.csv data/synthetic/pedidos.csv
COPY deploy/start-api.py .
USER ops
CMD ["python", "start-api.py"]
