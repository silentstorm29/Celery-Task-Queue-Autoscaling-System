# Celery Task Queue Autoscaling System (Minikube)

Autoscaling Celery workers on **queue depth** using **Kubernetes HPA (External metrics)** with **Prometheus + Prometheus Adapter**.  
Includes CPU- and I/O-bound tasks, a Redis-backed queue, a queue-depth exporter, and load generators.

---

## TL;DR (Minikube)
```bash
minikube start --cpus=4 --memory=6g
minikube addons enable metrics-server

# Build images inside Minikube for fast local loop
eval $(minikube -p minikube docker-env)
docker build -t celery-autoscale-app:local -f app/Dockerfile .
docker build -t celery-queue-exporter:local -f exporter/Dockerfile .

# Deploy
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s

# Drive load from your laptop
kubectl -n celery-autoscale port-forward svc/redis 6379:6379 &
python3 -m venv .venv && source .venv/bin/activate && pip install celery redis
BROKER_URL=redis://127.0.0.1:6379/0 BACKEND_URL=redis://127.0.0.1:6379/1 \
  python scripts/generate_tasks.py burst --n 400

# Watch it scale
watch -n 3 kubectl -n celery-autoscale get hpa,deploy,pods
Using GHCR images from CI? Set the images via kustomize before apply:

bash
Copy
Edit
cd k8s
kustomize edit set image \
  celery-autoscale-app=ghcr.io/silentstorm29/Celery-Task-Queue-Autoscaling-System/celery-autoscale-app:<SHORT_SHA> \
  celery-queue-exporter=ghcr.io/silentstorm29/Celery-Task-Queue-Autoscaling-System/celery-queue-exporter:<SHORT_SHA>
kubectl apply -f 00-namespace.yaml
kustomize build . | kubectl apply -f -
Architecture
sql
Copy
Edit
+------------------+     tasks     +---------------------------+
| Task Generator   |  -----------> | Redis (broker + backend)  |
+------------------+               +---------------------------+
        ^                                   ^
        |                                   |
        |  metrics (Prom)                   | Celery queue
        |                                   |
+--------------------------+         +-------------------------+
| Celery Worker Pods (HPA) |<--------| Queue Exporter (FastAPI)|
| cpu_bound / io_bound     |  /metrics -> celery_queue_depth   |
| task metrics exposed     |                                  |
+--------------------------+                                  |
            ^                                                 |
            | scrape                                          |
      +-----------+          metrics          +-----------------------+
      |Prometheus | ------------------------> | Prometheus Adapter    |
      +-----------+                           +-----------------------+
                                                     |
                                                     v
                                            HPA (External metric)
Autoscaling: the signal & policy
External metric: celery_queue_depth (Redis LLEN of celery queue)

Target: AverageValue: 10 → aim ~10 queued items per worker

Policies:

Scale up: +200% every 15s (no stabilization)

Scale down: −50% every 30s with stabilizationWindowSeconds: 60

Worker concurrency: default 2 (tune in 02-worker.yaml)

Repository Layout
bash
Copy
Edit
app/        # Celery app, tasks, Prom metrics, Dockerfile
exporter/   # Queue depth exporter (FastAPI), Dockerfile
scripts/    # Task generator: burst/ramp/oscillate
k8s/        # Namespace, Redis, Worker, Exporter, Prometheus, Adapter, HPA, RBAC, kustomization.yaml
.github/workflows/  # build.yml (GHCR), integration.yml (KinD autoscaling test)
Observability
Worker metrics: celery_task_success_total, celery_task_failure_total, celery_task_duration_seconds_*

Queue metrics: celery_queue_depth, celery_queue_exporter_last_poll_ok

Inspect Prometheus:

bash
Copy
Edit
kubectl -n celery-autoscale port-forward svc/prometheus 9090:9090
# http://localhost:9090
# Example queries:
#   celery_queue_depth
#   rate(celery_task_success_total[1m])
#   histogram_quantile(0.95, sum(rate(celery_task_duration_seconds_bucket[5m])) by (le, task_name))
Mapping to Deliverables
Celery app w/ multiple task types: app/tasks.py (CPU + I/O)

Broker: Redis (k8s/01-redis.yaml)

Metrics: worker Prom metrics + queue-depth exporter

Autoscaling: HPA on external metric (k8s/06-hpa.yaml)

Task generation: scripts/generate_tasks.py (burst/ramp/oscillate)

K8s/Minikube configs: k8s/ + kustomization.yaml

Docs: this README; CI, Stretch & Performance in docs/ (see below)

Troubleshooting (top issues)
HPA shows Unknown: metrics-server not healthy or adapter not ready. Check:

kubectl -n kube-system get pods | grep metrics-server

kubectl -n celery-autoscale logs deploy/prometheus-adapter

No scaling despite load: confirm Prometheus sees celery_queue_depth. Check exporter logs:

kubectl -n celery-autoscale logs deploy/queue-exporter

Images won’t pull (CI/KinD): ensure GHCR tags exist for the current SHA, or make packages public / add a pull secret.

CI & Stretch (optional)
CI/KinD pipeline and autoscaling assertions → see docs/CI.md

Priority queues, Grafana dashboards, routing strategies → see docs/Stretch.md

Performance analysis template + queries → see docs/Performance.md