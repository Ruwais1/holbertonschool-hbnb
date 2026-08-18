# HBnB Part 2 — Testing and Validation Report

**Execution date:** 2026-07-14  
**Environment:** Python 3.13.5, Flask 3.1.3, Flask-RESTX 1.3.2  
**API base URL:** `http://127.0.0.1:5000/api/v1`

## 1. Scope

This task validates the `User`, `Amenity`, `Place`, and `Review` models and tests their REST endpoints. The implementation includes:

- Model-level validation.
- Consistent `400 Bad Request` responses for invalid input.
- `404 Not Found` responses for missing resources.
- Positive, negative, boundary, and relationship tests.
- Swagger/OpenAPI verification.
- Automated `unittest` coverage.
- Manual black-box tests using `cURL`.

## 2. Implemented validation rules

### User

- `first_name` and `last_name` must be non-empty strings.
- Names must be at most 50 characters.
- `email` must be non-empty and match a basic email format.
- Email addresses must be unique.
- `password` is optional for Part 2; when supplied, it cannot be empty.
- Updates are atomic: invalid changes do not corrupt the existing object.

### Amenity

- `name` must be a non-empty string.
- `name` must be at most 50 characters.
- Updates are validated and atomic.

### Place

- `title` must be non-empty and at most 100 characters.
- `price` must be a positive number.
- `latitude` must be between `-90` and `90`, inclusive.
- `longitude` must be between `-180` and `180`, inclusive.
- `owner_id` must reference an existing user.
- Every amenity ID must reference an existing amenity.
- Updates are validated and atomic.

### Review

- `text` must be a non-empty string.
- `rating` must be an integer from `1` to `5`.
- `user_id` and `place_id` must reference existing entities.
- A user cannot submit more than one review for the same place.
- Only review text and rating can be updated.
- Deleting a review also removes it from the related place.

## 3. Automated test execution

Command:

```bash
python3 -m unittest discover -s tests -v
```

Actual result:

```text
Ran 41 tests in 0.272s

OK
```

### Automated test coverage summary

| Area | Successful cases | Invalid and edge cases |
|---|---|---|
| User | Create, list, get, update | Empty names, invalid email, duplicate email, missing user |
| Amenity | Create, list, get, update | Empty name, excessive length, missing amenity |
| Place | Create, list, get, partial update | Missing owner, missing amenity, zero/negative price, invalid coordinates, missing place |
| Review | Create, list, get, update, delete | Empty text, rating below 1 or above 5, invalid references, duplicate review, missing review |
| Swagger | UI and JSON schema available | Required API paths checked |
| Models | Valid construction and updates | Type checks, boundary checks, atomic rollback |

## 4. Manual cURL test execution

The script assumes the Flask server is running:

```bash
python3 run.py
```

In another terminal:

```bash
bash curl_tests.sh
```

Actual result:

```text
PASS  Swagger UI is available                        HTTP 200
PASS  Create a valid owner                           HTTP 201
PASS  Reject invalid user data                       HTTP 400
PASS  Create a valid reviewer                        HTTP 201
PASS  Create a valid amenity                         HTTP 201
PASS  Reject an empty amenity name                   HTTP 400
PASS  Create a valid place                           HTTP 201
PASS  Reject a non-positive price                    HTTP 400
PASS  Reject out-of-range latitude                   HTTP 400
PASS  Create a valid review                          HTTP 201
PASS  Reject a rating outside 1-5                    HTTP 400
PASS  Return 404 for a missing place                 HTTP 404
PASS  List reviews for a place                       HTTP 200
PASS  Update a review                                HTTP 200
PASS  Delete a review                                HTTP 200

Summary: 15 passed, 0 failed
```

## 5. Representative test matrix

| Test | Endpoint | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| Valid user | `POST /users/` | Valid names and email | `201` | `201` | Pass |
| Invalid user | `POST /users/` | Empty name and malformed email | `400` | `400` | Pass |
| Duplicate email | `POST /users/` | Existing email | `400` | `400` | Pass |
| Valid amenity | `POST /amenities/` | `{"name": "Wi-Fi"}` | `201` | `201` | Pass |
| Empty amenity | `POST /amenities/` | Empty name | `400` | `400` | Pass |
| Valid place | `POST /places/` | Valid owner, price, coordinates | `201` | `201` | Pass |
| Zero price | `POST /places/` | `price: 0` | `400` | `400` | Pass |
| Latitude boundary | `POST /places/` | `latitude: -90` or `90` | `201` | `201` | Pass |
| Invalid latitude | `POST /places/` | `latitude: 91` | `400` | `400` | Pass |
| Missing place | `GET /places/not-a-real-id` | Unknown ID | `404` | `404` | Pass |
| Valid review | `POST /reviews/` | Valid text, rating, references | `201` | `201` | Pass |
| Invalid rating | `POST /reviews/` | `rating: 6` | `400` | `400` | Pass |
| Duplicate review | `POST /reviews/` | Same user and place | `400` | `400` | Pass |
| Update review | `PUT /reviews/<id>` | New text and rating | `200` | `200` | Pass |
| Delete review | `DELETE /reviews/<id>` | Existing review ID | `200` | `200` | Pass |

## 6. Swagger verification

Swagger UI is generated automatically by Flask-RESTX and is available at:

```text
http://127.0.0.1:5000/api/v1/
```

The raw OpenAPI document is available at:

```text
http://127.0.0.1:5000/swagger.json
```

The automated suite verifies that Swagger loads successfully and contains the registered user and place paths.

## 7. Issues found and corrected

- User endpoint validation errors previously could become server errors instead of `400`.
- User updates previously returned `201` and a plain string; they now return `200` and the updated object.
- Review rating validation used an impossible condition and accepted invalid ratings.
- Review references were not validated consistently in the business layer.
- Review deletion previously reported success even for a missing review.
- Place price previously allowed zero despite the positive-price requirement.
- Place updates used the full creation schema, preventing valid partial updates.
- Generic repository updates bypassed entity validation.
- `BaseModel.to_dict()` expected datetime objects while timestamps were stored as floats.
- Review serialization mixed nested objects with fields named `user_id` and `place_id`.

## 8. Final status

All required model validations, automated tests, cURL black-box tests, error cases, boundary cases, and Swagger checks were implemented and executed successfully.
