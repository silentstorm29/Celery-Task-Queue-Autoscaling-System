import time, math, random, httpx
from celery import shared_task
from prometheus_client import Counter, Histogram

TASK_SUCCESS = Counter("celery_task_success_total", "Total successful Celery tasks", ["task_name"])
TASK_FAILURE = Counter("celery_task_failure_total", "Total failed Celery tasks", ["task_name"])
TASK_DURATION = Histogram("celery_task_duration_seconds", "Duration of Celery tasks", ["task_name"])

def _sleep_ms(ms: int):
    time.sleep(ms / 1000.0)

@shared_task(bind=True, name="tasks.cpu_bound")
def cpu_bound(self, complexity: int = 30_000):
    task = "cpu_bound"
    start = time.time()
    try:
        acc = 0.0
        for i in range(1, complexity):
            acc += math.sqrt(i) * math.sin(i)
        TASK_SUCCESS.labels(task).inc()
        return {"ok": True, "acc": acc}
    except Exception as e:
        TASK_FAILURE.labels(task).inc()
        raise e
    finally:
        TASK_DURATION.labels(task).observe(time.time() - start)

@shared_task(bind=True, name="tasks.io_bound")
def io_bound(self, url: str = "https://example.com", min_delay_ms: int = 100, max_delay_ms: int = 500):
    task = "io_bound"
    start = time.time()
    try:
        try:
            with httpx.Client(timeout=2.0) as client:
                try: client.get(url)
                except Exception: pass
        finally:
            _sleep_ms(random.randint(min_delay_ms, max_delay_ms))
        TASK_SUCCESS.labels(task).inc()
        return {"ok": True, "url": url}
    except Exception as e:
        TASK_FAILURE.labels(task).inc()
        raise e
    finally:
        TASK_DURATION.labels(task).observe(time.time() - start)
