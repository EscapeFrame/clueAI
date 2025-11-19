#!/bin/bash
# Run the FastAPI application using the virtual environment

.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
