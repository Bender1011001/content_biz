import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Service settings
CONTENT_PRICE = float(os.getenv("CONTENT_PRICE", "75.0"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "70.0"))

# API settings
API_PREFIX = "/api"
PROJECT_NAME = "AI Content Creation Service"
