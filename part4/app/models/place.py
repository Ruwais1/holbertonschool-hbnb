"""Place model and place/amenity association."""

from app.models.basemodel import BaseModel
from app.models.user import User
from extention import db


place_amenity = db.Table(
    "place_amenity",
    db.Column(
        "place_id", db.String(36), db.ForeignKey("places.id"), primary_key=True
    ),
    db.Column(
        "amenity_id",
        db.String(36),
        db.ForeignKey("amenities.id"),
        primary_key=True,
    ),
)


class Place(BaseModel):
    __tablename__ = "places"

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    owner_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )

    owner = db.relationship("User", backref="places")
    reviews = db.relationship(
        "Review", backref="place", lazy=True, cascade="all, delete-orphan"
    )
    amenities = db.relationship(
        "Amenity",
        secondary=place_amenity,
        lazy="subquery",
        backref=db.backref("places", lazy=True),
    )

    def __init__(
        self,
        title,
        price,
        latitude,
        longitude,
        owner,
        description="",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.price = price
        self.latitude = latitude
        self.longitude = longitude
        if not isinstance(owner, User):
            raise ValueError("owner must be a User")
        self.owner = owner
        self.owner_id = owner.id
        self.validate()

    def validate(self):
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")
        if len(self.title) > 100:
            raise ValueError("title must be at most 100 characters")
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("description must be a string")
        if isinstance(self.price, bool) or not isinstance(self.price, (int, float)):
            raise ValueError("price must be a number")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if isinstance(self.latitude, bool) or not isinstance(
            self.latitude, (int, float)
        ):
            raise ValueError("latitude must be a number")
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if isinstance(self.longitude, bool) or not isinstance(
            self.longitude, (int, float)
        ):
            raise ValueError("longitude must be a number")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        if not isinstance(self.owner, User):
            raise ValueError("owner must be a User")

    def add_review(self, review):
        from app.models.review import Review

        if not isinstance(review, Review):
            raise ValueError("review must be a Review")
        if review.place is not self:
            raise ValueError("review must reference this place")
        if review not in self.reviews:
            self.reviews.append(review)
            self.save()
        return review

    def add_amenity(self, amenity):
        from app.models.amenity import Amenity

        if not isinstance(amenity, Amenity):
            raise ValueError("amenity must be an Amenity")
        if amenity not in self.amenities:
            self.amenities.append(amenity)
            self.save()
        return amenity

    def add_amenities(self, amenity):
        return self.add_amenity(amenity)

    def remove_review(self, review):
        if review in self.reviews:
            self.reviews.remove(review)
            self.save()

    def remove_amenities(self, amenity):
        if amenity in self.amenities:
            self.amenities.remove(amenity)
            self.save()

    def updatePlace(self, data):
        return self.update(data)
