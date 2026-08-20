"""Black-box API tests for authentication, authorization, and validation."""

import unittest

from app import create_app
from app.services import facade
from config import TestingConfig
from extention import db


class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestingConfig)
        cls.context = cls.app.app_context()
        cls.context.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.context.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.admin = self.create_user(
            "admin@example.com", "adminpass", is_admin=True
        )
        self.owner = self.create_user("owner@example.com", "ownerpass")
        self.other = self.create_user("other@example.com", "otherpass")
        self.reviewer = self.create_user(
            "reviewer@example.com", "reviewpass"
        )
        self.admin_headers = self.login("admin@example.com", "adminpass")
        self.owner_headers = self.login("owner@example.com", "ownerpass")
        self.other_headers = self.login("other@example.com", "otherpass")
        self.reviewer_headers = self.login(
            "reviewer@example.com", "reviewpass"
        )

    def create_user(self, email, password, is_admin=False):
        return facade.create_user({
            "first_name": email.split("@")[0].title(),
            "last_name": "User",
            "email": email,
            "password": password,
            "is_admin": is_admin,
        })

    def login(self, email, password):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        return {
            "Authorization": f"Bearer {response.get_json()['access_token']}"
        }

    def create_amenity(self, name="Wi-Fi"):
        response = self.client.post(
            "/api/v1/amenities/",
            headers=self.admin_headers,
            json={"name": name},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def create_place(self, headers=None, **overrides):
        payload = {
            "title": "Seaside Apartment",
            "description": "Close to the beach",
            "price": 150,
            "latitude": 24.7136,
            "longitude": 46.6753,
            "amenities": [],
        }
        payload.update(overrides)
        response = self.client.post(
            "/api/v1/places/",
            headers=headers or self.owner_headers,
            json=payload,
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def create_review(self, place_id, headers=None, **overrides):
        payload = {
            "text": "Excellent stay",
            "rating": 5,
            "place_id": place_id,
        }
        payload.update(overrides)
        response = self.client.post(
            "/api/v1/reviews/",
            headers=headers or self.reviewer_headers,
            json=payload,
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def test_application_root_and_swagger_are_available(self):
        root = self.client.get("/")
        self.assertEqual(root.status_code, 200)
        self.assertEqual(root.get_json()["message"], "HBnB API is running")
        self.assertEqual(self.client.get("/api/v1/").status_code, 200)
        schema = self.client.get("/swagger.json").get_json()
        self.assertIn("/api/v1/users/{user_id}", schema["paths"])
        self.assertIn("UserResponse", schema["definitions"])
        self.assertIn("ReviewResponse", schema["definitions"])

    def test_login_accepts_valid_and_rejects_invalid_passwords(self):
        invalid = self.client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "wrong"},
        )
        self.assertEqual(invalid.status_code, 401)
        valid = self.client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "ownerpass"},
        )
        self.assertEqual(valid.status_code, 200)

    def test_admin_can_create_user_with_hashed_password(self):
        response = self.client.post(
            "/api/v1/users/",
            headers=self.admin_headers,
            json={
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "password": "newpass",
            },
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertNotIn("password", response.get_json())
        stored = facade.get_user_by_email("new@example.com")
        self.assertNotEqual(stored.password, "newpass")
        self.assertTrue(stored.verify_password("newpass"))

    def test_non_admin_cannot_create_users(self):
        response = self.client.post(
            "/api/v1/users/",
            headers=self.owner_headers,
            json={
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "password": "newpass",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_user_creation_validates_input_and_unique_email(self):
        invalid = self.client.post(
            "/api/v1/users/",
            headers=self.admin_headers,
            json={
                "first_name": "",
                "last_name": "User",
                "email": "bad-email",
                "password": "pass",
            },
        )
        self.assertEqual(invalid.status_code, 400)
        duplicate = self.client.post(
            "/api/v1/users/",
            headers=self.admin_headers,
            json={
                "first_name": "Duplicate",
                "last_name": "User",
                "email": self.owner.email,
                "password": "pass",
            },
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_user_can_update_own_names(self):
        response = self.client.put(
            f"/api/v1/users/{self.owner.id}",
            headers=self.owner_headers,
            json={"first_name": "Updated"},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["first_name"], "Updated")

    def test_user_cannot_update_another_user(self):
        response = self.client.put(
            f"/api/v1/users/{self.other.id}",
            headers=self.owner_headers,
            json={"first_name": "Hacked"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    def test_user_cannot_change_email_or_password(self):
        response = self.client.put(
            f"/api/v1/users/{self.owner.id}",
            headers=self.owner_headers,
            json={"email": "changed@example.com"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "You cannot modify email or password",
        )

    def test_admin_can_update_any_user_email_and_password(self):
        response = self.client.put(
            f"/api/v1/users/{self.owner.id}",
            headers=self.admin_headers,
            json={
                "email": "updated-owner@example.com",
                "password": "updatedpass",
            },
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertNotIn("password", response.get_json())
        self.assertEqual(
            self.login("updated-owner@example.com", "updatedpass").keys(),
            {"Authorization"},
        )

    def test_admin_amenity_management_and_invalid_atomic_update(self):
        amenity = self.create_amenity()
        updated = self.client.put(
            f"/api/v1/amenities/{amenity['id']}",
            headers=self.admin_headers,
            json={"name": "Fast Wi-Fi"},
        )
        self.assertEqual(updated.status_code, 200)
        invalid = self.client.put(
            f"/api/v1/amenities/{amenity['id']}",
            headers=self.admin_headers,
            json={"name": ""},
        )
        self.assertEqual(invalid.status_code, 400)
        stored = self.client.get(f"/api/v1/amenities/{amenity['id']}")
        self.assertEqual(stored.get_json()["name"], "Fast Wi-Fi")

    def test_non_admin_cannot_manage_amenities(self):
        response = self.client.post(
            "/api/v1/amenities/",
            headers=self.owner_headers,
            json={"name": "Pool"},
        )
        self.assertEqual(response.status_code, 403)

    def test_place_creation_uses_authenticated_owner(self):
        amenity = self.create_amenity()
        place = self.create_place(amenities=[amenity["id"]])
        self.assertEqual(place["owner"]["id"], self.owner.id)
        self.assertEqual(place["amenities"][0]["id"], amenity["id"])

    def test_place_creation_rejects_invalid_values(self):
        for field, value in [
            ("price", 0),
            ("price", -1),
            ("latitude", 91),
            ("longitude", -181),
        ]:
            payload = {
                "title": "House",
                "price": 100,
                "latitude": 0,
                "longitude": 0,
            }
            payload[field] = value
            with self.subTest(field=field, value=value):
                response = self.client.post(
                    "/api/v1/places/",
                    headers=self.owner_headers,
                    json=payload,
                )
                self.assertEqual(response.status_code, 400)

    def test_place_partial_update_is_atomic_and_updates_timestamp(self):
        place = self.create_place()
        before = place["updated_at"]
        updated = self.client.put(
            f"/api/v1/places/{place['id']}",
            headers=self.owner_headers,
            json={"price": 200},
        )
        self.assertEqual(updated.status_code, 200, updated.get_json())
        self.assertEqual(updated.get_json()["price"], 200)
        self.assertNotEqual(updated.get_json()["updated_at"], before)

        invalid = self.client.put(
            f"/api/v1/places/{place['id']}",
            headers=self.owner_headers,
            json={"title": "Changed", "price": 0},
        )
        self.assertEqual(invalid.status_code, 400)
        stored = self.client.get(f"/api/v1/places/{place['id']}").get_json()
        self.assertEqual(stored["title"], "Seaside Apartment")
        self.assertEqual(stored["price"], 200)

    def test_non_owner_cannot_update_or_delete_place(self):
        place = self.create_place()
        update = self.client.put(
            f"/api/v1/places/{place['id']}",
            headers=self.other_headers,
            json={"title": "Hacked"},
        )
        self.assertEqual(update.status_code, 403)
        self.assertEqual(update.get_json()["error"], "Unauthorized action")
        delete = self.client.delete(
            f"/api/v1/places/{place['id']}",
            headers=self.other_headers,
        )
        self.assertEqual(delete.status_code, 403)

    def test_owner_and_admin_can_delete_places(self):
        owner_place = self.create_place(title="Owner place")
        admin_place = self.create_place(title="Admin-deleted place")
        owner_delete = self.client.delete(
            f"/api/v1/places/{owner_place['id']}",
            headers=self.owner_headers,
        )
        self.assertEqual(owner_delete.status_code, 200)
        admin_delete = self.client.delete(
            f"/api/v1/places/{admin_place['id']}",
            headers=self.admin_headers,
        )
        self.assertEqual(admin_delete.status_code, 200)

    def test_review_creation_returns_ids_and_validates_data(self):
        place = self.create_place()
        review = self.create_review(place["id"])
        self.assertEqual(review["user_id"], self.reviewer.id)
        self.assertEqual(review["place_id"], place["id"])
        for text, rating in [("", 5), ("Bad", 0), ("Bad", 6)]:
            response = self.client.post(
                "/api/v1/reviews/",
                headers=self.other_headers,
                json={"text": text, "rating": rating, "place_id": place["id"]},
            )
            self.assertEqual(response.status_code, 400)

    def test_review_rejects_missing_place_duplicate_and_own_place(self):
        missing = self.client.post(
            "/api/v1/reviews/",
            headers=self.reviewer_headers,
            json={"text": "Good", "rating": 4, "place_id": "missing"},
        )
        self.assertEqual(missing.status_code, 400)
        place = self.create_place()
        self.create_review(place["id"])
        duplicate = self.client.post(
            "/api/v1/reviews/",
            headers=self.reviewer_headers,
            json={"text": "Again", "rating": 3, "place_id": place["id"]},
        )
        self.assertEqual(duplicate.status_code, 400)
        own = self.client.post(
            "/api/v1/reviews/",
            headers=self.owner_headers,
            json={"text": "Mine", "rating": 5, "place_id": place["id"]},
        )
        self.assertEqual(own.status_code, 400)

    def test_non_author_cannot_update_or_delete_review(self):
        review = self.create_review(self.create_place()["id"])
        update = self.client.put(
            f"/api/v1/reviews/{review['id']}",
            headers=self.other_headers,
            json={"rating": 1},
        )
        self.assertEqual(update.status_code, 403)
        self.assertEqual(update.get_json()["error"], "Unauthorized action")
        delete = self.client.delete(
            f"/api/v1/reviews/{review['id']}",
            headers=self.other_headers,
        )
        self.assertEqual(delete.status_code, 403)

    def test_review_author_can_update_with_validation(self):
        review = self.create_review(self.create_place()["id"])
        update = self.client.put(
            f"/api/v1/reviews/{review['id']}",
            headers=self.reviewer_headers,
            json={"text": "Updated", "rating": 4},
        )
        self.assertEqual(update.status_code, 200, update.get_json())
        self.assertEqual(update.get_json()["rating"], 4)
        invalid = self.client.put(
            f"/api/v1/reviews/{review['id']}",
            headers=self.reviewer_headers,
            json={"rating": 6},
        )
        self.assertEqual(invalid.status_code, 400)
        stored = self.client.get(f"/api/v1/reviews/{review['id']}")
        self.assertEqual(stored.get_json()["rating"], 4)

    def test_review_delete_removes_it_from_place(self):
        place = self.create_place()
        review = self.create_review(place["id"])
        deleted = self.client.delete(
            f"/api/v1/reviews/{review['id']}",
            headers=self.reviewer_headers,
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/v1/reviews/{review['id']}").status_code,
            404,
        )
        place_reviews = self.client.get(
            f"/api/v1/places/{place['id']}/reviews"
        )
        self.assertEqual(place_reviews.get_json(), [])

    def test_missing_resources_return_404(self):
        self.assertEqual(
            self.client.get("/api/v1/users/missing").status_code, 404
        )
        self.assertEqual(
            self.client.get("/api/v1/places/missing").status_code, 404
        )
        self.assertEqual(
            self.client.get("/api/v1/reviews/missing").status_code, 404
        )
        self.assertEqual(
            self.client.delete(
                "/api/v1/reviews/missing", headers=self.admin_headers
            ).status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
