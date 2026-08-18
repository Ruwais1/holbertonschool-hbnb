"""Module For review"""
from extention import db
from app.models.basemodel import BaseModel

# Inherit from BaseModel and db.Model to map this class to a database table
class Review(BaseModel, db.Model):
    """Review class mapped to the 'reviews' table"""
    __tablename__ = 'reviews'

    # SQLAlchemy Columns
    text = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    
    # Foreign Keys linking to users and places tables
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    place_id = db.Column(db.String(36), db.ForeignKey('places.id'), nullable=False)
    user = db.relationship('User', backref='user_reviews')

    def __init__(self, text=None, rating=None, place=None, user=None, user_id=None, place_id=None, **kwargs):
        """Initialize function"""
        super().__init__(**kwargs)
        if text is not None:
            self.text = text
        if rating is not None:
            self.rating = rating

        # Handle user object or user_id string
        if user:
            self.user_id = user.id if hasattr(user, 'id') else user
        elif user_id:
            self.user_id = user_id

        # Handle place object or place_id string
        if place:
            self.place_id = place.id if hasattr(place, 'id') else place
        elif place_id:
            self.place_id = place_id

        self.validate()

    def validate(self):
        """Validate function"""
        if not isinstance(self.text, str) or self.text.strip() == "":
            raise ValueError("text is required")
            
        if not isinstance(self.rating, int) or not (1 <= self.rating <= 5):
            raise ValueError("rating rquired between 1 and 5")
