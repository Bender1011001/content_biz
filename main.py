import logging
import os
import uvicorn
import sqlalchemy as sa
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import config # Import the config module
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
    # Pass the Stripe Publishable Key to the template context
    context = {
        "request": request,
        "stripe_publishable_key": config.STRIPE_PUBLISHABLE_KEY 
    }
    if not config.STRIPE_PUBLISHABLE_KEY:
        logger.warning("STRIPE_PUBLISHABLE_KEY is not set in the environment.")
        # Optionally handle the case where the key is missing, e.g., show an error
        # For now, we'll pass None or an empty string, but the JS needs to handle this.
        context["stripe_publishable_key"] = "" 
        
    return templates.TemplateResponse("form.html", context)

@app.get("/payment-success", response_class=HTMLResponse)
async def payment_success(request: Request, brief_id: str = None):
    """Render the payment success page."""
    logger.debug(f"Payment success page requested for brief_id: {brief_id}")
    context = {
        "request": request,
        "brief_id": brief_id
    }
    return templates.TemplateResponse("payment-success.html", context)

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
    import os
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting development server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
