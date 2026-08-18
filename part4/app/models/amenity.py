"""Amenity model"""
from extention import db
from app.models.basemodel import BaseModel

# Inherit from BaseModel and db.Model to map this class to a database table
class Amenity(BaseModel, db.Model):
    """Amenity class mapped to the 'amenities' table"""
    __tablename__ = 'amenities'

    # SQLAlchemy Column
    name = db.Column(db.String(50), nullable=False)

    def __init__(self, name=None, **kwargs):
        """Initialize amenity instance"""
        super().__init__(**kwargs)
        if name is not None:
            self.name = name
        self.validate()

    def validate(self):
        """Validate amenity attributes"""
        if not isinstance(self.name, str) or self.name.strip() == "":
            raise ValueError("name cannot be empty")

        if len(self.name) > 50:
            raise ValueError("maximum length for name is 50")

    def update(self, data):
        """Update amenity attributes"""
        if "name" in data:
            self.name = data["name"]

        self.validate()
        self.save()
