"""Unit tests for HBnB model validation."""

import unittest

from app.models.amenity import Amenity
from app.models.place import Place
from app.models.review import Review
from app.models.user import User


class UserModelTests(unittest.TestCase):
    def test_valid_user_without_password(self):
        user = User("Jane", "Doe", "jane.doe@example.com")
        self.assertEqual(user.first_name, "Jane")
        self.assertIsNone(user.password)

    def test_user_required_names(self):
        for field, values in {
            "first_name": ["", "   ", None],
            "last_name": ["", "   ", None],
        }.items():
            for value in values:
                data = {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@example.com",
                }
                data[field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        User(**data)

    def test_user_name_length_limit(self):
        with self.assertRaises(ValueError):
            User("x" * 51, "Doe", "jane@example.com")
        with self.assertRaises(ValueError):
            User("Jane", "x" * 51, "jane@example.com")

    def test_user_email_format(self):
        invalid_emails = [
            "",
            "plain-address",
            "missing-at.example.com",
            "missing-domain@",
            "@missing-local.com",
            "has space@example.com",
        ]
        for email in invalid_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    User("Jane", "Doe", email)

    def test_user_update_is_atomic(self):
        user = User("Jane", "Doe", "jane@example.com")
        with self.assertRaises(ValueError):
            user.update({"email": "bad-email"})
        self.assertEqual(user.email, "jane@example.com")


class AmenityModelTests(unittest.TestCase):
    def test_valid_amenity(self):
        self.assertEqual(Amenity("Wi-Fi").name, "Wi-Fi")

    def test_amenity_name_validation(self):
        for name in ["", "   ", None, "x" * 51]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Amenity(name)


class PlaceModelTests(unittest.TestCase):
    def setUp(self):
        self.owner = User("Owner", "One", "owner@example.com")

    def test_valid_place_and_boundaries(self):
        place = Place(
            title="Boundary House",
            description="Valid coordinates",
            price=1,
            latitude=-90,
            longitude=180,
            owner=self.owner,
        )
        self.assertEqual(place.latitude, -90)
        self.assertEqual(place.longitude, 180)

    def test_place_requires_title(self):
        for title in ["", "   ", None, "x" * 101]:
            with self.subTest(title=title):
                with self.assertRaises(ValueError):
                    Place(title, 100, 0, 0, self.owner)

    def test_place_price_must_be_positive(self):
        for price in [0, -1, "100", True]:
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    Place("House", price, 0, 0, self.owner)

    def test_place_latitude_range(self):
        for latitude in [-90.01, 90.01, "0", True]:
            with self.subTest(latitude=latitude):
                with self.assertRaises(ValueError):
                    Place("House", 100, latitude, 0, self.owner)

    def test_place_longitude_range(self):
        for longitude in [-180.01, 180.01, "0", True]:
            with self.subTest(longitude=longitude):
                with self.assertRaises(ValueError):
                    Place("House", 100, 0, longitude, self.owner)

    def test_place_requires_user_owner(self):
        with self.assertRaises(ValueError):
            Place("House", 100, 0, 0, "not-a-user")

    def test_place_update_is_atomic(self):
        place = Place("House", 100, 0, 0, self.owner)
        with self.assertRaises(ValueError):
            place.update({"price": 0})
        self.assertEqual(place.price, 100)


class ReviewModelTests(unittest.TestCase):
    def setUp(self):
        self.user = User("Jane", "Doe", "jane@example.com")
        self.place = Place("House", 100, 0, 0, self.user)

    def test_valid_review(self):
        review = Review("Excellent stay", 5, self.place, self.user)
        self.assertEqual(review.rating, 5)

    def test_review_text_required(self):
        for text in ["", "   ", None]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    Review(text, 5, self.place, self.user)

    def test_review_rating_range(self):
        for rating in [0, 6, 2.5, "5", True]:
            with self.subTest(rating=rating):
                with self.assertRaises(ValueError):
                    Review("Good", rating, self.place, self.user)

    def test_review_references_are_valid(self):
        with self.assertRaises(ValueError):
            Review("Good", 4, self.place, "not-a-user")
        with self.assertRaises(ValueError):
            Review("Good", 4, "not-a-place", self.user)

    def test_review_update_is_atomic(self):
        review = Review("Good", 4, self.place, self.user)
        with self.assertRaises(ValueError):
            review.update({"rating": 7})
        self.assertEqual(review.rating, 4)


class BaseModelTests(unittest.TestCase):
    def test_to_dict_uses_iso_timestamps(self):
        data = User("Jane", "Doe", "jane@example.com").to_dict()
        self.assertIn("T", data["created_at"])
        self.assertIn("T", data["updated_at"])


if __name__ == "__main__":
    unittest.main()
