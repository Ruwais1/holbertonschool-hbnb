"""Black-box style endpoint tests using Flask's test client."""

import unittest

from app import create_app
from app.persistence.repository import InMemoryRepository
from app.services import facade


class APITestCase(unittest.TestCase):
    def setUp(self):
        # The application uses a module-level facade; reset every repository so
        # each test is independent and repeatable.
        facade.user_repo = InMemoryRepository()
        facade.place_repo = InMemoryRepository()
        facade.review_repo = InMemoryRepository()
        facade.amenity_repo = InMemoryRepository()

        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def create_user(self, email="owner@example.com"):
        response = self.client.post(
            "/api/v1/users/",
            json={
                "first_name": "Owner",
                "last_name": "One",
                "email": email,
            },
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def create_amenity(self, name="Wi-Fi"):
        response = self.client.post(
            "/api/v1/amenities/",
            json={"name": name},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def create_place(self, owner_id, amenity_ids=None, **overrides):
        payload = {
            "title": "Seaside Apartment",
            "description": "Close to the beach",
            "price": 150.0,
            "latitude": 24.7136,
            "longitude": 46.6753,
            "owner_id": owner_id,
            "amenities": amenity_ids or [],
        }
        payload.update(overrides)
        response = self.client.post("/api/v1/places/", json=payload)
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def test_swagger_documentation_is_available(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HBnB API", response.data)

        schema = self.client.get("/swagger.json")
        self.assertEqual(schema.status_code, 200)
        paths = schema.get_json()["paths"]
        self.assertIn("/api/v1/users/", paths)
        self.assertIn("/api/v1/places/", paths)

    def test_create_and_list_users(self):
        user = self.create_user()
        self.assertNotIn("password", user)

        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    def test_invalid_user_data_returns_400(self):
        invalid_payloads = [
            {"first_name": "", "last_name": "Doe", "email": "jane@example.com"},
            {"first_name": "Jane", "last_name": "", "email": "jane@example.com"},
            {"first_name": "Jane", "last_name": "Doe", "email": "bad-email"},
            {"first_name": "Jane", "last_name": "Doe"},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/v1/users/", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_duplicate_email_returns_400(self):
        self.create_user()
        response = self.client.post(
            "/api/v1/users/",
            json={
                "first_name": "Other",
                "last_name": "Person",
                "email": "owner@example.com",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already registered", response.get_json()["error"])

    def test_get_and_update_user(self):
        user = self.create_user()

        get_response = self.client.get(f"/api/v1/users/{user['id']}")
        self.assertEqual(get_response.status_code, 200)

        update_response = self.client.put(
            f"/api/v1/users/{user['id']}",
            json={"first_name": "Updated"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["first_name"], "Updated")

    def test_user_not_found_returns_404(self):
        response = self.client.get("/api/v1/users/missing")
        self.assertEqual(response.status_code, 404)
        response = self.client.put(
            "/api/v1/users/missing",
            json={"first_name": "Updated"},
        )
        self.assertEqual(response.status_code, 404)

    def test_create_list_and_update_amenity(self):
        amenity = self.create_amenity()

        list_response = self.client.get("/api/v1/amenities/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.get_json()), 1)

        update_response = self.client.put(
            f"/api/v1/amenities/{amenity['id']}",
            json={"name": "Fast Wi-Fi"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["name"], "Fast Wi-Fi")

    def test_invalid_amenity_returns_400(self):
        response = self.client.post("/api/v1/amenities/", json={"name": ""})
        self.assertEqual(response.status_code, 400)

    def test_amenity_not_found_returns_404(self):
        response = self.client.get("/api/v1/amenities/missing")
        self.assertEqual(response.status_code, 404)

    def test_create_and_list_places(self):
        owner = self.create_user()
        amenity = self.create_amenity()
        place = self.create_place(owner["id"], [amenity["id"]])

        self.assertEqual(place["owner"]["id"], owner["id"])
        self.assertEqual(place["amenities"][0]["id"], amenity["id"])

        response = self.client.get("/api/v1/places/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    def test_place_requires_existing_owner_and_amenities(self):
        payload = {
            "title": "House",
            "price": 100,
            "latitude": 0,
            "longitude": 0,
            "owner_id": "missing",
        }
        response = self.client.post("/api/v1/places/", json=payload)
        self.assertEqual(response.status_code, 400)

        owner = self.create_user()
        payload["owner_id"] = owner["id"]
        payload["amenities"] = ["missing"]
        response = self.client.post("/api/v1/places/", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_place_boundary_and_required_validation(self):
        owner = self.create_user()
        invalid_values = [
            ("title", ""),
            ("price", 0),
            ("price", -1),
            ("latitude", -91),
            ("latitude", 91),
            ("longitude", -181),
            ("longitude", 181),
        ]
        for field, value in invalid_values:
            payload = {
                "title": "House",
                "price": 100,
                "latitude": 0,
                "longitude": 0,
                "owner_id": owner["id"],
            }
            payload[field] = value
            with self.subTest(field=field, value=value):
                response = self.client.post("/api/v1/places/", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_place_accepts_coordinate_boundaries(self):
        owner = self.create_user()
        lower = self.create_place(
            owner["id"],
            title="Lower",
            latitude=-90,
            longitude=-180,
        )
        upper = self.create_place(
            owner["id"],
            title="Upper",
            latitude=90,
            longitude=180,
        )
        self.assertEqual(lower["latitude"], -90)
        self.assertEqual(upper["longitude"], 180)

    def test_partial_place_update_and_atomic_validation(self):
        owner = self.create_user()
        place = self.create_place(owner["id"])

        response = self.client.put(
            f"/api/v1/places/{place['id']}",
            json={"price": 200},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["price"], 200)

        invalid = self.client.put(
            f"/api/v1/places/{place['id']}",
            json={"price": 0},
        )
        self.assertEqual(invalid.status_code, 400)

        get_response = self.client.get(f"/api/v1/places/{place['id']}")
        self.assertEqual(get_response.get_json()["price"], 200)

    def test_place_not_found_returns_404(self):
        response = self.client.get("/api/v1/places/missing")
        self.assertEqual(response.status_code, 404)
        response = self.client.put(
            "/api/v1/places/missing",
            json={"title": "New"},
        )
        self.assertEqual(response.status_code, 404)

    def test_create_and_list_reviews(self):
        owner = self.create_user("owner@example.com")
        reviewer = self.create_user("reviewer@example.com")
        place = self.create_place(owner["id"])

        response = self.client.post(
            "/api/v1/reviews/",
            json={
                "text": "Excellent stay",
                "rating": 5,
                "user_id": reviewer["id"],
                "place_id": place["id"],
            },
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        review = response.get_json()
        self.assertEqual(review["user_id"], reviewer["id"])

        list_response = self.client.get("/api/v1/reviews/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.get_json()), 1)

        place_reviews = self.client.get(
            f"/api/v1/places/{place['id']}/reviews"
        )
        self.assertEqual(place_reviews.status_code, 200)
        self.assertEqual(len(place_reviews.get_json()), 1)

    def test_review_validation_returns_400(self):
        owner = self.create_user("owner@example.com")
        reviewer = self.create_user("reviewer@example.com")
        place = self.create_place(owner["id"])

        invalid_cases = [
            {"text": "", "rating": 5},
            {"text": "Bad rating", "rating": 0},
            {"text": "Bad rating", "rating": 6},
        ]
        for invalid in invalid_cases:
            payload = {
                "text": invalid["text"],
                "rating": invalid["rating"],
                "user_id": reviewer["id"],
                "place_id": place["id"],
            }
            with self.subTest(payload=payload):
                response = self.client.post("/api/v1/reviews/", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_review_requires_existing_references(self):
        owner = self.create_user("owner@example.com")
        reviewer = self.create_user("reviewer@example.com")
        place = self.create_place(owner["id"])

        response = self.client.post(
            "/api/v1/reviews/",
            json={
                "text": "Good",
                "rating": 4,
                "user_id": "missing",
                "place_id": place["id"],
            },
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/api/v1/reviews/",
            json={
                "text": "Good",
                "rating": 4,
                "user_id": reviewer["id"],
                "place_id": "missing",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_review_returns_400(self):
        owner = self.create_user("owner@example.com")
        reviewer = self.create_user("reviewer@example.com")
        place = self.create_place(owner["id"])
        payload = {
            "text": "Good",
            "rating": 4,
            "user_id": reviewer["id"],
            "place_id": place["id"],
        }
        self.assertEqual(
            self.client.post("/api/v1/reviews/", json=payload).status_code,
            201,
        )
        response = self.client.post("/api/v1/reviews/", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_update_and_delete_review(self):
        owner = self.create_user("owner@example.com")
        reviewer = self.create_user("reviewer@example.com")
        place = self.create_place(owner["id"])
        created = self.client.post(
            "/api/v1/reviews/",
            json={
                "text": "Good",
                "rating": 4,
                "user_id": reviewer["id"],
                "place_id": place["id"],
            },
        ).get_json()

        update = self.client.put(
            f"/api/v1/reviews/{created['id']}",
            json={"text": "Excellent", "rating": 5},
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["rating"], 5)

        delete = self.client.delete(f"/api/v1/reviews/{created['id']}")
        self.assertEqual(delete.status_code, 200)

        missing = self.client.get(f"/api/v1/reviews/{created['id']}")
        self.assertEqual(missing.status_code, 404)

        place_reviews = self.client.get(
            f"/api/v1/places/{place['id']}/reviews"
        )
        self.assertEqual(place_reviews.get_json(), [])

    def test_review_not_found_returns_404(self):
        self.assertEqual(
            self.client.get("/api/v1/reviews/missing").status_code,
            404,
        )
        self.assertEqual(
            self.client.put(
                "/api/v1/reviews/missing",
                json={"rating": 5},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete("/api/v1/reviews/missing").status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
