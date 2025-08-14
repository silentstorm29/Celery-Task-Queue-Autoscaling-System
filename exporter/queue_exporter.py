import os, redis
from fastapi import FastAPI, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_KEY = os.getenv("QUEUE_KEY", os.getenv("CELERY_QUEUE_KEY", "celery"))
r = redis.from_url(REDIS_URL, decode_responses=False)
app = FastAPI()

queue_depth = Gauge("celery_queue_depth", "Current length of the Celery queue")
last_poll_ok = Gauge("celery_queue_exporter_last_poll_ok", "1 if last Redis poll ok, else 0")

@app.get("/healthz")
def healthz():
    try:
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return Response(content=str(e), status_code=500)

@app.get("/metrics")
def metrics():
    try:
        depth = r.llen(QUEUE_KEY)
        queue_depth.set(depth)
        last_poll_ok.set(1)
    except Exception:
        last_poll_ok.set(0)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
