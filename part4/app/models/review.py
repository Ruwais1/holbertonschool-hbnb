"""Review model."""

from app.models.basemodel import BaseModel
from extention import db


class Review(BaseModel):
    __tablename__ = "reviews"
    __table_args__ = (
        db.UniqueConstraint("user_id", "place_id", name="uq_review_user_place"),
    )

    text = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    place_id = db.Column(
        db.String(36), db.ForeignKey("places.id"), nullable=False, index=True
    )
    user = db.relationship("User", backref="user_reviews")

    def __init__(self, text, rating, place, user, **kwargs):
        from app.models.place import Place
        from app.models.user import User

        super().__init__(**kwargs)
        self.text = text
        self.rating = rating
        self._validate_content()
        if not isinstance(user, User):
            raise ValueError("user must be a User")
        if not isinstance(place, Place):
            raise ValueError("place must be a Place")
        self.user = user
        self.user_id = user.id
        self.place = place
        self.place_id = place.id
        self.validate()

    def validate(self):
        from app.models.place import Place
        from app.models.user import User

        self._validate_content()
        if not isinstance(self.user, User):
            raise ValueError("user must be a User")
        if not isinstance(self.place, Place):
            raise ValueError("place must be a Place")

    def _validate_content(self):
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text is required")
        if (
            isinstance(self.rating, bool)
            or not isinstance(self.rating, int)
            or not 1 <= self.rating <= 5
        ):
            raise ValueError("rating must be an integer between 1 and 5")
