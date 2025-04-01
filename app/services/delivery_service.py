import logging
import os
import smtplib
from datetime import datetime
from sqlalchemy.orm import Session
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from ..db.models import Content, Brief  # Added Brief import

logger = logging.getLogger(__name__)


# New function for sending email via SendGrid or SMTP
def send_content_email(email: str, content_text: str):
    """
    Sends the generated content text to the client's email.
    Uses SendGrid if SENDGRID_API_KEY is available, otherwise falls back to SMTP.
    """
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    smtp_user = os.getenv("EMAIL_USERNAME")  # Updated to match config.py variable name
    smtp_pass = os.getenv("EMAIL_PASSWORD")  # Updated to match config.py variable name
    from_email = os.getenv("EMAIL_FROM") or smtp_user or "noreply@contentbiz.com" # Use configured sender, or username, or default

    try:
        if sendgrid_api_key:
            logger.info(f"Sending email to {email} via SendGrid")
            sg = SendGridAPIClient(sendgrid_api_key)
            message = Mail(
                from_email=from_email, # Consider using a verified SendGrid sender
                to_emails=email,
                subject="Your Content is Ready!",
                plain_text_content=content_text
            )
            response = sg.send(message)
            logger.info(f"SendGrid response status code: {response.status_code}")
            if response.status_code >= 300:
                 logger.error(f"SendGrid error: {response.body}")
                 raise Exception(f"SendGrid failed with status {response.status_code}")
        elif smtp_user and smtp_pass:
            logger.info(f"Sending email to {email} via SMTP")
            smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("EMAIL_PORT", "587"))
            with smtplib.SMTP(smtp_host, smtp_port) as server: # Using environment variables
                server.starttls()
                server.login(smtp_user, smtp_pass)
                message = f"Subject: Your Content is Ready!\n\n{content_text}"
                # Ensure message is properly encoded, especially if content might have non-ASCII chars
                server.sendmail(from_email, email, message.encode('utf-8'))
            logger.info("Email sent successfully via SMTP")
        else:
            logger.warning("Email not sent: Neither SendGrid API key nor SMTP credentials configured.")
            # Optionally raise an error or return a specific status
            return False # Indicate failure due to configuration

        return True # Indicate success

    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        return False # Indicate failure


# Existing DeliveryService class

class DeliveryService:
    """Service for delivering generated content to clients"""
    
    @staticmethod
    def mark_as_delivered(content_id: str, db: Session):
        """
        Mark content as delivered in the database.
        
        Args:
            content_id: The ID of the content to mark as delivered
            db: SQLAlchemy database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                logger.error(f"Content with ID {content_id} not found")
                return False
            
            content.delivery_status = "delivered"
            content.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Content {content_id} marked as delivered")
            return True
        except Exception as e:
            logger.error(f"Error marking content as delivered: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    async def deliver_content(content_id: str, db: Session):
        """
        Deliver content to client via email.
        
        Args:
            content_id: The ID of the content to deliver
            db: SQLAlchemy database session
            
        Returns:
            Dictionary with delivery status
        """
        try:
            # In a real implementation, this would use the email service
            # to send the content to the client
            content = db.query(Content).filter(Content.id == content_id).first()
            if not content:
                logger.error(f"Content with ID {content_id} not found")
                return {
                    "success": False,
                    "message": f"Content with ID {content_id} not found"
                }
            
            brief = content.brief
            client = brief.client
            
            # Log the delivery
            logger.info(f"Delivering content {content_id} to {client.email}")
            
            # Mark as delivered
            content.delivery_status = "delivered"
            db.commit()
            
            return {
                "success": True,
                "content_id": content_id,
                "client_email": client.email,
                "delivered_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error delivering content: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "message": str(e)
            }
