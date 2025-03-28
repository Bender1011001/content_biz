from sqlalchemy.orm import Session
from . import models

def get_or_create_client(db: Session, email: str, name: str):
    """Get an existing client or create a new one if it doesn't exist."""
    client = db.query(models.Client).filter(models.Client.email == email).first()
    if client:
        return client
    
    new_client = models.Client(email=email, name=name)
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client
