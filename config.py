import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
# SERPER_API_KEY = os.getenv("SERPER_API_KEY") # Removed as it's not currently used/configured

# JWT Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_dev_secret_key_change_me") # Default for local dev if not set
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Email Service
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# Service settings
CONTENT_PRICE = float(os.getenv("CONTENT_PRICE", "75.0"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "0.85")) # Default updated to 0.85

# Application settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development") # Default to development if not set
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# API settings
API_PREFIX = "/api"
PROJECT_NAME = "Premium Content Service" # Updated project name
