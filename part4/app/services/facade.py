"""Business-logic facade for the HBnB application."""

from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.models.user import User
from app.persistence.repository import (
    AmenityRepository,
    PlaceRepository,
    ReviewRepository,
    UserRepository,
)
from extention import db


class HBnBFacade:
    def __init__(self):
        self.user_repo = UserRepository()
        self.place_repo = PlaceRepository()
        self.review_repo = ReviewRepository()
        self.amenity_repo = AmenityRepository()

    def create_user(self, user_data):
        data = dict(user_data)
        if self.get_user_by_email(data.get("email")):
            raise ValueError("Email already registered")
        password = data.pop("password", None)
        user = User(password=password, **data)
        user.hash_password(password)
        return self.user_repo.add(user)

    def get_user(self, user_id):
        return self.user_repo.get(user_id)

    def get_user_by_email(self, email):
        if hasattr(self.user_repo, "get_user_by_email"):
            return self.user_repo.get_user_by_email(email)
        return self.user_repo.get_by_attribute("email", email)

    def get_alluser(self):
        return self.user_repo.get_all()

    def update_user(self, user_id, user_data):
        user = self.get_user(user_id)
        if not user:
            return None
        data = dict(user_data)
        unexpected = set(data) - {
            "first_name",
            "last_name",
            "email",
            "password",
            "is_admin",
        }
        if unexpected:
            raise ValueError("Invalid user fields")
        email = data.get("email")
        existing = self.get_user_by_email(email) if email else None
        if existing and existing.id != user_id:
            raise ValueError("Email already registered")
        has_password = "password" in data
        password = data.pop("password", None)
        if has_password:
            if not isinstance(password, str) or not password.strip():
                raise ValueError("password must be a non-empty string")
        if data:
            user.update(data)
        if has_password:
            user.hash_password(password)
            user.save()
        if hasattr(self.user_repo, "_commit"):
            self.user_repo._commit()
        return user

    def create_amenity(self, amenity_data):
        data = dict(amenity_data)
        existing = self.amenity_repo.get_by_attribute(
            "name", data.get("name")
        )
        if existing:
            raise ValueError("Amenity already exists")
        return self.amenity_repo.add(Amenity(**data))

    def get_amenity(self, amenity_id):
        return self.amenity_repo.get(amenity_id)

    def get_all_amenities(self):
        return self.amenity_repo.get_all()

    def update_amenity(self, amenity_id, amenity_data):
        data = dict(amenity_data)
        existing = self.amenity_repo.get_by_attribute(
            "name", data.get("name")
        )
        if existing and existing.id != amenity_id:
            raise ValueError("Amenity already exists")
        return self.amenity_repo.update(amenity_id, data)

    def create_place(self, place_data):
        data = dict(place_data)
        owner = self.get_user(data.pop("owner_id", None))
        if not owner:
            raise ValueError("Owner not found")
        amenities = self._resolve_amenities(data.pop("amenities", []))
        place = Place(owner=owner, **data)
        for amenity in amenities:
            place.add_amenity(amenity)
        return self.place_repo.add(place)

    def get_place(self, place_id):
        return self.place_repo.get(place_id)

    def get_all_places(self):
        return self.place_repo.get_all()

    def get_reviews_by_place(self, place_id):
        place = self.get_place(place_id)
        return None if not place else place.reviews

    def update_place(self, place_id, place_data):
        place = self.get_place(place_id)
        if not place:
            return None
        data = dict(place_data)
        if "owner_id" in data:
            raise ValueError("owner_id cannot be modified")
        amenities = None
        if "amenities" in data:
            amenities = self._resolve_amenities(data.pop("amenities"))
        allowed = {"title", "description", "price", "latitude", "longitude"}
        if set(data) - allowed:
            raise ValueError("Invalid place fields")
        try:
            if data:
                place.update(data)
            if amenities is not None:
                place.amenities = amenities
                place.save()
            if hasattr(self.place_repo, "_commit"):
                self.place_repo._commit()
        except (TypeError, ValueError):
            db.session.rollback()
            raise
        return place

    def delete_place(self, place_id):
        return self.place_repo.delete(place_id)

    def create_review(self, review_data):
        data = dict(review_data)
        user = self.get_user(data.pop("user_id", None))
        place = self.get_place(data.pop("place_id", None))
        if not user or not place:
            raise ValueError("User or place not found")
        duplicate = None
        if hasattr(self.review_repo, "get_by_user_and_place"):
            duplicate = self.review_repo.get_by_user_and_place(user.id, place.id)
        else:
            duplicate = next(
                (
                    review
                    for review in self.review_repo.get_all()
                    if review.user_id == user.id
                    and review.place_id == place.id
                ),
                None,
            )
        if duplicate:
            raise ValueError("You have already reviewed this place")
        review = Review(user=user, place=place, **data)
        return self.review_repo.add(review)

    def get_review(self, review_id):
        return self.review_repo.get(review_id)

    def get_all_reviews(self):
        return self.review_repo.get_all()

    def update_review(self, review_id, review_data):
        data = dict(review_data)
        if set(data) - {"text", "rating"}:
            raise ValueError("Only text and rating can be updated")
        return self.review_repo.update(review_id, data)

    def delete_review(self, review_id):
        return self.review_repo.delete(review_id)

    def password_hash(self, password):
        """Compatibility helper; user creation hashes passwords automatically."""
        user = User("Temp", "User", "temp@example.com", password)
        user.hash_password(password)
        return user.password

    def _resolve_amenities(self, amenity_ids):
        if not isinstance(amenity_ids, list):
            raise ValueError("amenities must be a list of IDs")
        amenities = []
        for amenity_id in amenity_ids:
            amenity = self.get_amenity(amenity_id)
            if not amenity:
                raise ValueError("Amenity not found")
            if amenity not in amenities:
                amenities.append(amenity)
        return amenities
