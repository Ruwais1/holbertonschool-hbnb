# HBnB Part 4 — Testing and Validation Report

**Execution date:** 2026-08-18

**Environment:** Python 3.14.6, Flask 3.1.3, Flask-RESTX 1.3.2,
Flask-SQLAlchemy 3.1.1

**API base URL:** `http://127.0.0.1:5000/api/v1`

## Scope

The suite verifies configuration switching, SQLAlchemy mappings, dedicated
repositories, model validation, password hashing, authentication,
authorization, CRUD endpoints, relationship integrity, atomic updates, and
Swagger output.

## Automated results

Command:

```bash
python -m unittest discover -s test -v
```

Recorded result:

```text
Ran 42 tests in 2.153s

OK
```

### Coverage matrix

| Area | Successful cases | Invalid/security cases |
|---|---|---|
| Configuration | Development, testing, and production classes load | Settings differ by environment |
| SQLAlchemy | Abstract `BaseModel`, entity tables, timestamps | Protected base fields rejected |
| Repositories | Dedicated user/place/review/amenity repositories | Missing records handled safely |
| Users/auth | Login, admin creation/update, own profile update | Duplicate/invalid email, bad password, cross-user update, restricted fields |
| Passwords | Hash stored, valid password verified | Plaintext never returned; invalid password rejected |
| Amenities | Admin create and update | Non-admin blocked; invalid update remains atomic |
| Places | Owner create/update/delete; admin delete | Invalid price/coordinates; non-owner blocked; atomic rollback |
| Reviews | Author create/update/delete; IDs serialized correctly | Invalid rating/text/reference, duplicate, own-place review, non-author blocked |
| Swagger | UI, OpenAPI paths, request and response schemas | Documented status/error responses |

## Required authorization behavior

| Operation | Allowed | Rejected result |
|---|---|---|
| Update another user's profile | Admin only | `403 {"error": "Unauthorized action"}` |
| Change email/password | Admin only | `400 {"error": "You cannot modify email or password"}` for regular users |
| Create/update amenity | Admin only | `403` for regular users |
| Update/delete place | Owner or admin | `403 {"error": "Unauthorized action"}` |
| Update/delete review | Author or admin | `403 {"error": "Unauthorized action"}` |

## Manual black-box test

With `python run.py` active, execute:

```bash
bash curl_tests.sh
```

The script logs in as the seeded administrator, creates authenticated users,
tests admin restrictions, creates a place and review, checks invalid input and
ownership enforcement, then updates and deletes the review.

Recorded result:

```text
Summary: 20 passed, 0 failed
```

## Corrections verified

- `create_app()` now loads the supplied configuration class.
- `BaseModel` inherits from `db.Model` and is abstract.
- User, Place, Review, and Amenity repositories extend
  `SQLAlchemyRepository`; `UserRepository.get_user_by_email()` is used by the
  Facade.
- Password hashing is performed in the business layer and has dedicated
  tests.
- Authorization compares JWT identity to stored ownership, never to a client
  field.
- User, place, amenity, and review updates validate before committing and
  restore prior values on failure.
- Review responses contain ID strings, deletion is accurate, and database
  relationships remain synchronized.
- Swagger defines separate create/update/response schemas.
- The Mermaid ER source has visually verified SVG and PNG exports.
