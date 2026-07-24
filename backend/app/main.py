from fastapi import FastAPI

app = FastAPI(
    title="Lagovia Train Tracker API",
    description="Thin layer on top of iRail API for Lagovia station departure tracking",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "ok"}
