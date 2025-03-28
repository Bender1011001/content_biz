import logging
import os
import uvicorn
import sqlalchemy as sa
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.api.router import api_router
from app.db.database import engine
from app.db.models import Base
from app.utils.logging import setup_logging

# Set up logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(title="Content Creation Service")

# Database setup is now handled by Alembic migrations.
# The old setup_database function is removed.

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page with the brief submission form."""
    logger.debug("Home page requested")
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/health")
def health_check():
    """Health check endpoint to verify the API is running."""
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting AI Content Creation Service...")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down AI Content Creation Service...")

if __name__ == "__main__":
    logger.info("Starting development server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
