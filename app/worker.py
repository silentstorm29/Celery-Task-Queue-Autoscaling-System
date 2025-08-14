import os
from prometheus_client import start_http_server
from celery_app import celery_app  # noqa
import tasks  # noqa

METRICS_PORT = int(os.getenv("METRICS_PORT", "9100"))

if __name__ == "__main__":
    start_http_server(METRICS_PORT)
    # Celery worker started by k8s command/args
