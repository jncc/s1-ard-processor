#!/bin/bash

virtualenv -p python3 /app/eo-s1-workflows-venv 
source /app/eo-s1-workflows-venv/bin/activate
pip install -r /app/workflows/requirements.txt