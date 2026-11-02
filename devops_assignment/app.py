"""A small FastAPI service for the DevOps CI/CD assignment."""

from fastapi import FastAPI

app = FastAPI(title="DevOps Python Service", version="1.0.0")


@app.get("/")
def home():
    """Return a friendly message from the service."""
    return {
        "service": "DevOps Python Service",
        "message": "Hello! The Python service is running inside a Docker container.",
        "status": "success",
    }


@app.get("/health")
def health():
    """Health-check endpoint used by Docker and the assignment demo."""
    return {"status": "healthy"}


@app.get("/api/info")
def info():
    """Return basic service information."""
    return {
        "application": "devops-python-service",
        "version": "1.0.0",
        "framework": "FastAPI",
        "runtime": "Docker",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
