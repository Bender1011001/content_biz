import stripe
import os
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

# Get Stripe API key from environment variable
stripe_key = os.getenv("STRIPE_SECRET_KEY")
print(f"Using Stripe API key from env: {stripe_key}")
print(f"Key length: {len(stripe_key) if stripe_key else 0}")
print(f"First 10 chars: {stripe_key[:10]}...{stripe_key[-4:]}")

# Set Stripe API key
stripe.api_key = stripe_key

try:
    # Try to list customers
    customers = stripe.Customer.list(limit=1)
    print("Success! Customers:", customers)
except Exception as e:
    print(f"Error: {e}")
