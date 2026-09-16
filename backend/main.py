from fastapi import FastAPI

app = FastAPI(
    title="AYUSHMED AI API",
    description="Backend API for AYUSHMED AI",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "AYUSHMED AI Backend is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }