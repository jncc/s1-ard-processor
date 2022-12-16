#!/bin/bash
umask 002
source /app/.venv/bin/activate
cd /app/workflows
PYTHONPATH='.' luigi --module process_s1_scene "$@" --local-scheduler
python /app/CopyState.py
