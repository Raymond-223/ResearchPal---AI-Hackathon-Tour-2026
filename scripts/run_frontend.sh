#!/usr/bin/env bash
set -e
export BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
python frontend/gradio_app.py