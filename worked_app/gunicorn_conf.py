import multiprocessing
import os

# Bind address
bind = os.getenv("BIND", "0.0.0.0:8000")

# Use Uvicorn workers for ASGI apps
worker_class = "uvicorn.workers.UvicornWorker"

# Worker count (default: CPU cores * 2 + 1)
_default = multiprocessing.cpu_count() * 2 + 1
workers = int(os.getenv("WORKERS", _default))

# Timeout settings
timeout = int(os.getenv("TIMEOUT", 30))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", 30))
keepalive = int(os.getenv("KEEPALIVE", 5))

# Logging
accesslog = "-"
errorlog = "-"