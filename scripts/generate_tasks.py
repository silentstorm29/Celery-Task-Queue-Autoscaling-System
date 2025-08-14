import os, argparse, random, time
from celery import Celery

BROKER_URL = os.getenv("BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("BACKEND_URL", "redis://localhost:6379/1")
celery_app = Celery("generator", broker=BROKER_URL, backend=BACKEND_URL)

def burst(n: int, cpu_ratio: float = 0.5):
    for _ in range(n):
        if random.random() < cpu_ratio:
            celery_app.send_task("tasks.cpu_bound", kwargs={"complexity": random.randint(20_000, 80_000)})
        else:
            celery_app.send_task("tasks.io_bound", kwargs={"min_delay_ms": 50, "max_delay_ms": 500})

def ramp(total: int, steps: int = 10, delay_s: float = 2.0):
    per_step = total // steps
    for _ in range(steps):
        burst(per_step, cpu_ratio=0.6)
        time.sleep(delay_s)

def oscillate(cycles: int = 5, low: int = 10, high: int = 80, period_s: float = 4.0):
    for _ in range(cycles):
        burst(low, cpu_ratio=0.4); time.sleep(period_s)
        burst(high, cpu_ratio=0.7); time.sleep(period_s)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("burst"); b.add_argument("--n", type=int, default=100)
    r = sub.add_parser("ramp"); r.add_argument("--total", type=int, default=200); r.add_argument("--steps", type=int, default=10); r.add_argument("--delay", type=float, default=2.0)
    o = sub.add_parser("oscillate"); o.add_argument("--cycles", type=int, default=5); o.add_argument("--low", type=int, default=10); o.add_argument("--high", type=int, default=80); o.add_argument("--period", type=float, default=4.0)
    args = ap.parse_args()
    {"burst": burst(args.n), "ramp": ramp(args.total, args.steps, args.delay), "oscillate": oscillate(args.cycles, args.low, args.high, args.period)}[args.mode]
