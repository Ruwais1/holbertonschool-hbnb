# HBnB Evolution — Part 3

## Authentication, Authorization & Database Persistence

Part 3 of **HBnB Evolution** extends the backend with JWT-based authentication, role-based access control, and persistent database storage using SQLAlchemy. The application is built with Python, Flask, Flask-RESTX, SQLAlchemy, and Flask-JWT-Extended, following the same layered architecture from Part 2.

The API manages five main resources:

- Users (with admin role support)
- Amenities
- Places
- Reviews
- Authentication (login/register)

Data is now stored persistently in a SQLite database using SQLAlchemy ORM.

## Architecture

The application is organized into three layers:

1. **Presentation layer** — Flask-RESTX namespaces and API endpoints.
2. **Business logic layer** — Domain models and the `HBnBFacade` service.
3. **Persistence layer** — SQLAlchemy ORM with SQLite database.

The Facade pattern provides a single entry point between the API layer and the application's models and repositories.

## Features

- User registration and login with hashed passwords
- JWT token-based authentication
- Role-based access control (admin and regular users)
- Create, retrieve, list, and update users (admin-only for listing)
- Create, retrieve, list, and update amenities
- Create, retrieve, list, and update places
- Create, retrieve, list, update, and delete reviews
- Associate places with owners and amenities
- Associate reviews with users and places
- Validate model attributes and resource relationships
- Persistent storage using SQLite database
- Return appropriate HTTP status codes for invalid or missing resources
- Generate interactive Swagger documentation automatically
- Run automated unit and endpoint tests

## Project Structure

```text
part3/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── v1/
│   │       ├── amenities.py
│   │       ├── auth.py
│   │       ├── places.py
│   │       ├── reviews.py
│   │       └── users.py
│   ├── models/
│   │   ├── amenity.py
│   │   ├── basemodel.py
│   │   ├── place.py
│   │   ├── review.py
│   │   └── user.py
│   ├── persistence/
│   │   └── repository.py
│   └── services/
│       └── facade.py
├── instance/
│   └── development.db
├── test/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_models.py
├── config.py
├── extention.py
├── requirements.txt
├── run.py
└── README.md
```

## Requirements

- Python 3
- Flask
- Flask-RESTX
- Flask-JWT-Extended
- SQLAlchemy

## Installation

Clone the repository and move to the Part 3 directory:

```bash
git clone <repository-url>
cd holbertonschool-hbnb/part3
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

From the `part3` directory, run:

```bash
python3 run.py
```

The development server starts at:

```text
http://127.0.0.1:5000
```

The interactive Swagger documentation is available at:

```text
http://127.0.0.1:5000/api/v1/
```

The generated OpenAPI document is available at:

```text
http://127.0.0.1:5000/swagger.json
```

## API Endpoints

The API base path is `/api/v1`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Login and receive a JWT token |
| `POST` | `/auth/register` | Register a new user |

### Users

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/users/` | List all users (admin only) | Yes (Admin) |
| `GET` | `/users/<user_id>` | Retrieve a user | No |
| `PUT` | `/users/<user_id>` | Update a user | Yes (Owner) |

### Amenities

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/amenities/` | Create an amenity |
| `GET` | `/amenities/` | List all amenities |
| `GET` | `/amenities/<amenity_id>` | Retrieve an amenity |
| `PUT` | `/amenities/<amenity_id>` | Update an amenity |

### Places

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/places/` | Create a place |
| `GET` | `/places/` | List all places |
| `GET` | `/places/<place_id>` | Retrieve a place |
| `PUT` | `/places/<place_id>` | Update a place |
| `GET` | `/places/<place_id>/reviews` | List reviews for a place |

### Reviews

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reviews/` | Create a review |
| `GET` | `/reviews/` | List all reviews |
| `GET` | `/reviews/<review_id>` | Retrieve a review |
| `PUT` | `/reviews/<review_id>` | Update a review |
| `DELETE` | `/reviews/<review_id>` | Delete a review |

## Request Examples

### Register a User

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ali",
    "last_name": "Ahmed",
    "email": "ali@example.com",
    "password": "secure-password"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ali@example.com",
    "password": "secure-password"
  }'
```

### Create an Amenity (Authenticated)

```bash
curl -X POST http://127.0.0.1:5000/api/v1/amenities/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{"name": "Wi-Fi"}'
```

### Create a Place (Authenticated)

Replace `<user_id>` and `<amenity_id>` with IDs returned by the API.

```bash
curl -X POST http://127.0.0.1:5000/api/v1/places/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
    "title": "Seaside Apartment",
    "description": "Apartment close to the beach",
    "price": 150.0,
    "latitude": 24.7136,
    "longitude": 46.6753,
    "owner_id": "<user_id>",
    "amenities": ["<amenity_id>"]
  }'
```

### Create a Review (Authenticated)

Replace `<user_id>` and `<place_id>` with existing resource IDs.

```bash
curl -X POST http://127.0.0.1:5000/api/v1/reviews/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
    "text": "Excellent stay",
    "rating": 5,
    "user_id": "<user_id>",
    "place_id": "<place_id>"
  }'
```

## Validation Rules

| Resource | Main rules |
|---|---|
| User | Names are required and limited to 50 characters; email must be valid and unique; password is hashed |
| Amenity | Name is required and limited to 50 characters |
| Place | Title is required; price must be valid; latitude must be from `-90` to `90`; longitude must be from `-180` to `180`; owner and amenities must exist |
| Review | Text is required; rating must be an integer from `1` to `5`; user and place must exist |

Common response codes include:

- `200 OK` — Request completed successfully.
- `201 Created` — Resource created successfully.
- `400 Bad Request` — Invalid input or relationship.
- `401 Unauthorized` — Authentication failed or missing token.
- `403 Forbidden` — Insufficient permissions (admin required).
- `404 Not Found` — Requested resource does not exist.

## Running the Automated Tests

From the `part3` directory, run:

```bash
python3 -m unittest discover -s test -v
```

The test suite covers model validation, API operations, authentication, authorization, boundary values, missing resources, and invalid relationships.

## Persistence Note

Part 3 uses **SQLAlchemy** with a **SQLite** database (`instance/development.db`). All data is persisted on disk and survives application restarts. To reset the database, delete the `instance/development.db` file and restart the server.

## Authors

- Azzam Al Duyuli
- Fahad Almidaj
- Ali Alsayah
