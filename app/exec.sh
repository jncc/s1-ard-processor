#!/bin/bash
source /app/eo-s1-workflows-venv/bin/activate
cd /app/workflows
PYTHONPATH='.' luigi --module container.process_s1_scene Cleanup "$@" --removeSourceFile --local-scheduler
