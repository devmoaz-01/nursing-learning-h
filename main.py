"""Uvicorn entry point for NurseLearn.

Start the app from the project folder with:
    py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

from backend.app import app

__all__ = ["app"]
