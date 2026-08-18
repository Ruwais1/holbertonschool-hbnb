import uuid
from datetime import datetime
from extention import db

class BaseModel:
    """
    BaseModel defines common attributes/methods
    for all models in the application.
    It acts as a mixin for SQLAlchemy models.
    """
    
    # SQLAlchemy Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        """
        Initialize a new model instance
        """
        # If ID or timestamps are passed, use them, otherwise defaults handle it
        if 'id' in kwargs:
            self.id = kwargs['id']
        else:
            self.id = str(uuid.uuid4())
            
        if 'created_at' in kwargs:
            self.created_at = kwargs['created_at']
        else:
            self.created_at = datetime.utcnow()
            
        if 'updated_at' in kwargs:
            self.updated_at = kwargs['updated_at']
        else:
            self.updated_at = datetime.utcnow()

    def save(self):
        """
        Updates the updated_at timestamp.
        Note: Actual database saving is handled by the repository.
        """
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Returns a dictionary representation of the instance"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }

    def update(self, data):
        """Updates attributes based on a dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
