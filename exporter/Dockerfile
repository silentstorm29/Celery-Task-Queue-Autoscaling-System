FROM python:3.11-slim
WORKDIR /exporter
COPY exporter/requirements.txt /exporter/requirements.txt
RUN pip install --no-cache-dir -r /exporter/requirements.txt
COPY exporter /exporter
ENV PORT=8000
CMD ["uvicorn", "queue_exporter:app", "--host", "0.0.0.0", "--port", "8000"]
