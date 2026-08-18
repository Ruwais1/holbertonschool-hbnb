"""Module For place"""
from extention import db
from app.models.basemodel import BaseModel
from app.models.user import User

# Association table for Many-to-Many relationship between Place and Amenity
place_amenity = db.Table(
    'place_amenity',
    db.Column('place_id', db.String(36), db.ForeignKey('places.id'), primary_key=True),
    db.Column('amenity_id', db.String(36), db.ForeignKey('amenities.id'), primary_key=True)
)

# Inherit from BaseModel and db.Model
class Place(BaseModel, db.Model):
    """Place class mapped to the 'places' table"""
    __tablename__ = 'places'

    # SQLAlchemy Columns
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Foreign Key linking to users table (Owner)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Relationships
    owner = db.relationship('User', backref='places')
    reviews = db.relationship('Review', backref='place', lazy=True, cascade='all, delete-orphan')
    amenities = db.relationship('Amenity', secondary=place_amenity, lazy='subquery',
                                backref=db.backref('places', lazy=True))

    def __init__(self, title=None, price=None, latitude=None, longitude=None, owner=None, description="", **kwargs):
        """Initialize Place instance"""
        super().__init__(**kwargs)
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if price is not None:
            self.price = price
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude

        if owner:
            if isinstance(owner, User):
                self.owner = owner
                self.owner_id = owner.id
            elif isinstance(owner, str):
                self.owner_id = owner

        self.validate()

    def validate(self):
        """Validate Place attributes"""
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")

        if len(self.title) > 100:
            raise ValueError("title must be at most 100 characters")

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("description must be a string")

        if not isinstance(self.price, (int, float)):
            raise ValueError("price must be a number")

        if self.price < 0:
            raise ValueError("price must be non-negative")

        if not isinstance(self.latitude, (int, float)):
            raise ValueError("latitude must be a number")

        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")

        if not isinstance(self.longitude, (int, float)):
            raise ValueError("longitude must be a number")

        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")

        if not getattr(self, 'owner', None) and not getattr(self, 'owner_id', None):
            raise ValueError("owner must be a User")

    def add_review(self, review):
        """Add a review to the place"""
        if review not in self.reviews:
            self.reviews.append(review)

    def add_amenities(self, amenity):
        """Add an amenity to the place"""
        if amenity not in self.amenities:
            self.amenities.append(amenity)

    def remove_review(self, review):
        """Remove a review from the place"""
        if review in self.reviews:
            self.reviews.remove(review)

    def remove_amenities(self, amenity):
        """Remove an amenity from the place"""
        if amenity in self.amenities:
            self.amenities.remove(amenity)

    def updatePlace(self, data):
        """Update place attributes"""
        self.update(data)
        self.validate()
