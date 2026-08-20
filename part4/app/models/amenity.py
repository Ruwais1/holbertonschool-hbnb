"""Amenity model."""

from app.models.basemodel import BaseModel
from extention import db


class Amenity(BaseModel):
    __tablename__ = "amenities"

    name = db.Column(db.String(50), nullable=False, unique=True)

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.validate()

    def validate(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name cannot be empty")
        if len(self.name) > 50:
            raise ValueError("maximum length for name is 50")

    def update(self, data):
        if set(data) - {"name"}:
            raise ValueError("Only name can be updated")
        return super().update(data)
