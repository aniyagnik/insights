#!/bin/bash

celery -A app.worker.celery_app worker --loglevel=info &

celery -A app.worker.celery_app beat --loglevel=info &

uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}