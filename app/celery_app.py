import os
from celery import Celery

BROKER_URL = os.getenv("BROKER_URL", "redis://redis:6379/0")
BACKEND_URL = os.getenv("BACKEND_URL", "redis://redis:6379/1")

celery_app = Celery("autoscale_demo", broker=BROKER_URL, backend=BACKEND_URL)

celery_app.conf.task_queues = {"celery": {}}

celery_app.conf.update(
    task_default_queue=os.getenv("CELERY_DEFAULT_QUEUE", "celery"),
    task_routes={
        "tasks.cpu_bound": {"queue": os.getenv("CPU_QUEUE", "celery")},
        "tasks.io_bound": {"queue": os.getenv("IO_QUEUE", "celery")},
    },
    worker_prefetch_multiplier=int(os.getenv("WORKER_PREFETCH", "4")),
    task_acks_late=True,
    broker_connection_max_retries=None,
    broker_pool_limit=None,
    result_expires=3600,
)
