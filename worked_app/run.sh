#!/usr/bin/env bash
set -euo pipefail

# Optional environment variables
# export WORKERS=4
# export BIND=0.0.0.0:9000

exec gunicorn \
  -c gunicorn_conf.py \
  app.main:app