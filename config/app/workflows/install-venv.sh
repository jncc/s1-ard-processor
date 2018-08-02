#!/bin/bash

virtualenv -p python3 /app/eo-s1-workflow-venv 
source /app/eo-s1-workflow-venv/bin/activate
pip install -r /app/workflows/requirements.txt