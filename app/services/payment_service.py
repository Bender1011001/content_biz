import os
import logging
import stripe
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from ..db.models import Payment, Brief

# Set Stripe API key from environment variable
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") # Updated to match the config.py variable name

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(stripe.error.StripeError)
    )
    def create_payment_intent(stripe_customer_id, amount):
        """
        Create a payment intent in Stripe for the specified amount.
        
        Args:
            stripe_customer_id: The Stripe customer ID
            amount: The amount to charge in dollars
            
        Returns:
            The payment intent object
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                customer=stripe_customer_id,
                metadata={"integration_check": "content_creation_payment"}
            )
            logger.info(f"Created payment intent {payment_intent.id} for customer {stripe_customer_id}")
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment error: {str(e)}")
            # Rethrow for retry
            raise
        except Exception as e:
            logger.error(f"Unexpected error in payment processing: {str(e)}")
            raise
    
    @staticmethod
    def get_or_create_customer(email, name):
        """
        Get an existing Stripe customer or create a new one if it doesn't exist.
        
        Args:
            email: The customer's email
            name: The customer's name
            
        Returns:
            The Stripe customer ID
        """
        try:
            # Search for existing customer by email
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                logger.info(f"Found existing Stripe customer for {email}")
                return customers.data[0].id
            
            # Create new customer if not found
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            logger.info(f"Created new Stripe customer for {email}")
            return customer.id
        except Exception as e:
            logger.error(f"Error creating/finding Stripe customer: {str(e)}")
            raise
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id):
        """
        Get the status of a payment intent.
        
        Args:
            payment_intent_id: The ID of the payment intent to check
            
        Returns:
            True if the payment is successful, False otherwise
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent.status == "succeeded"
        except Exception as e:
            logger.error(f"Error confirming payment intent: {str(e)}")
            return False
