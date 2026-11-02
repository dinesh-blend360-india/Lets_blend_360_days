"""ASGI entry point for running the service with ``uvicorn main:app``."""

from app import app

__all__ = ["app"]
