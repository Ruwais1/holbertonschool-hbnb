"""Unit tests for Part 4 models, configuration, and repositories."""

import unittest

from app import create_app
from app.models.amenity import Amenity
from app.models.basemodel import BaseModel
from app.models.place import Place
from app.models.review import Review
from app.models.user import User
from app.persistence.repository import (
    AmenityRepository,
    PlaceRepository,
    ReviewRepository,
    SQLAlchemyRepository,
    UserRepository,
)
from app.services import facade
from config import DevelopmentConfig, ProductionConfig, TestingConfig
from extention import db


class ModelTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestingConfig)
        cls.context = cls.app.app_context()
        cls.context.push()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()

    def user(self, email="user@example.com", password="secret123"):
        return User("Jane", "Doe", email, password)

    def place(self, owner=None, **overrides):
        data = {
            "title": "House",
            "description": "A valid place",
            "price": 100,
            "latitude": 0,
            "longitude": 0,
            "owner": owner or self.user(),
        }
        data.update(overrides)
        return Place(**data)

    def test_configuration_classes_change_application_behavior(self):
        development = create_app(DevelopmentConfig)
        testing = create_app(TestingConfig)
        production = create_app(ProductionConfig)
        self.assertTrue(development.config["DEBUG"])
        self.assertTrue(testing.config["TESTING"])
        self.assertFalse(production.config["DEBUG"])
        self.assertNotEqual(
            development.config["SQLALCHEMY_DATABASE_URI"],
            testing.config["SQLALCHEMY_DATABASE_URI"],
        )

    def test_base_model_is_abstract_sqlalchemy_model(self):
        self.assertTrue(issubclass(BaseModel, db.Model))
        self.assertTrue(BaseModel.__abstract__)
        self.assertIn("id", User.__table__.columns)
        self.assertIn("created_at", User.__table__.columns)
        self.assertIn("updated_at", User.__table__.columns)

    def test_timestamps_and_to_dict(self):
        user = self.user()
        original = user.updated_at
        user.update({"first_name": "Updated"})
        self.assertGreater(user.updated_at, original)
        self.assertIn("T", user.to_dict()["created_at"])

    def test_protected_base_fields_cannot_be_updated(self):
        user = self.user()
        original = user.id
        with self.assertRaises(ValueError):
            user.update({"id": "replacement"})
        self.assertEqual(user.id, original)

    def test_valid_user_and_password_hashing(self):
        user = facade.create_user({
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "password": "secret123",
        })
        self.assertNotEqual(user.password, "secret123")
        self.assertTrue(user.verify_password("secret123"))
        self.assertFalse(user.verify_password("wrong"))

    def test_user_required_fields_and_name_limits(self):
        invalid = [
            ("", "Doe", "jane@example.com", "secret"),
            ("Jane", "", "jane@example.com", "secret"),
            ("x" * 51, "Doe", "jane@example.com", "secret"),
            ("Jane", "x" * 51, "jane@example.com", "secret"),
            ("Jane", "Doe", "jane@example.com", ""),
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                User(*values)

    def test_user_email_validation(self):
        for email in ["", "plain", "missing@", "@domain.com", "a b@c.com"]:
            with self.subTest(email=email), self.assertRaises(ValueError):
                self.user(email=email)

    def test_user_update_is_atomic(self):
        user = self.user()
        with self.assertRaises(ValueError):
            user.update({"first_name": "Valid", "email": "invalid"})
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.email, "user@example.com")

    def test_user_email_uniqueness_is_enforced(self):
        facade.create_user({
            "first_name": "One",
            "last_name": "User",
            "email": "same@example.com",
            "password": "secret",
        })
        with self.assertRaises(ValueError):
            facade.create_user({
                "first_name": "Two",
                "last_name": "User",
                "email": "same@example.com",
                "password": "secret",
            })

    def test_amenity_validation_and_atomic_update(self):
        amenity = Amenity("Wi-Fi")
        for name in ["", "   ", None, "x" * 51]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                amenity.update({"name": name})
            self.assertEqual(amenity.name, "Wi-Fi")

    def test_valid_place_and_coordinate_boundaries(self):
        lower = self.place(latitude=-90, longitude=-180)
        upper = self.place(latitude=90, longitude=180)
        self.assertEqual(lower.latitude, -90)
        self.assertEqual(upper.longitude, 180)

    def test_place_numeric_validation(self):
        invalid = [
            {"price": 0},
            {"price": -1},
            {"price": True},
            {"latitude": -91},
            {"latitude": 91},
            {"latitude": True},
            {"longitude": -181},
            {"longitude": 181},
            {"longitude": True},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.place(**values)

    def test_place_requires_valid_title_and_owner(self):
        with self.assertRaises(ValueError):
            self.place(title="")
        with self.assertRaises(ValueError):
            self.place(title="x" * 101)
        with self.assertRaises(ValueError):
            self.place(owner="not-a-user")

    def test_place_update_is_atomic(self):
        place = self.place()
        with self.assertRaises(ValueError):
            place.update({"title": "Changed", "price": 0})
        self.assertEqual(place.title, "House")
        self.assertEqual(place.price, 100)

    def test_place_relationship_helpers_validate_and_deduplicate(self):
        owner = self.user()
        place = self.place(owner=owner)
        amenity = Amenity("Pool")
        place.add_amenity(amenity)
        place.add_amenity(amenity)
        self.assertEqual(len(place.amenities), 1)
        with self.assertRaises(ValueError):
            place.add_amenity("Pool")

        reviewer = self.user("reviewer@example.com")
        review = Review("Good", 4, place, reviewer)
        place.add_review(review)
        place.add_review(review)
        self.assertEqual(len(place.reviews), 1)
        with self.assertRaises(ValueError):
            place.add_review("not-a-review")

    def test_review_validation(self):
        owner = self.user()
        place = self.place(owner=owner)
        reviewer = self.user("reviewer@example.com")
        for text, rating in [("", 5), ("Good", 0), ("Good", 6), ("Good", True)]:
            with self.subTest(text=text, rating=rating), self.assertRaises(ValueError):
                Review(text, rating, place, reviewer)
        with self.assertRaises(ValueError):
            Review("Good", 4, place, "not-a-user")
        with self.assertRaises(ValueError):
            Review("Good", 4, "not-a-place", reviewer)

    def test_review_update_is_atomic(self):
        reviewer = self.user("reviewer@example.com")
        review = Review("Good", 4, self.place(), reviewer)
        with self.assertRaises(ValueError):
            review.update({"text": "Changed", "rating": 6})
        self.assertEqual(review.text, "Good")
        self.assertEqual(review.rating, 4)

    def test_entity_repositories_extend_sqlalchemy_repository(self):
        for repository in (
            UserRepository,
            PlaceRepository,
            ReviewRepository,
            AmenityRepository,
        ):
            with self.subTest(repository=repository):
                self.assertTrue(issubclass(repository, SQLAlchemyRepository))

    def test_facade_uses_entity_repositories(self):
        self.assertIsInstance(facade.user_repo, UserRepository)
        self.assertIsInstance(facade.place_repo, PlaceRepository)
        self.assertIsInstance(facade.review_repo, ReviewRepository)
        self.assertIsInstance(facade.amenity_repo, AmenityRepository)

    def test_user_repository_email_query(self):
        created = facade.create_user({
            "first_name": "Repo",
            "last_name": "User",
            "email": "repo@example.com",
            "password": "secret",
        })
        self.assertEqual(
            facade.user_repo.get_user_by_email("repo@example.com").id,
            created.id,
        )


if __name__ == "__main__":
    unittest.main()
