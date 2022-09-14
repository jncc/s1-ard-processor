#!/bin/bash

python3.10 -m venv /app/.venv
source /app/.venv/bin/activate
pip install -r /app/workflows/requirements.txt