# HBnB Evolution — Part 4

Part 4 implements the authenticated HBnB REST API with Flask, Flask-RESTX,
JWT, bcrypt, and SQLAlchemy. It manages users, amenities, places, and reviews
through a layered API → Facade → Repository architecture.

## Main behavior

- The application factory accepts development, testing, or production
  configuration classes.
- Passwords are hashed with bcrypt and never appear in API responses.
- JWT identity and admin claims control protected operations.
- Users may update only their own names; admins may manage every user.
- Only admins may create or update amenities.
- Only a place owner or an admin may update or delete that place.
- Only a review author or an admin may update or delete that review.
- Model and Facade validation enforce valid fields, relationships, and atomic
  updates.
- Each entity uses a dedicated SQLAlchemy repository.

## Run the API

From this directory:

```bash
pip install -r requirements.txt
python run.py
```

Useful URLs:

- API status: `http://127.0.0.1:5000/`
- Swagger UI: `http://127.0.0.1:5000/api/v1/`
- OpenAPI JSON: `http://127.0.0.1:5000/swagger.json`

The seeded development administrator is:

- Email: `admin@hbnb.io`
- Password: `admin1234`

Set `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL` through environment
variables outside local development.

## Tests

Run the automated suite:

```bash
python -m unittest discover -s test -v
```

Run black-box requests while the server is active:

```bash
bash curl_tests.sh
```

See [`TESTING_REPORT.md`](TESTING_REPORT.md) for the coverage and recorded
results.

## Database artifacts

- [`schema.sql`](schema.sql) creates the relational schema.
- [`seed.sql`](seed.sql) inserts the default administrator and amenities.
- [`er_diagram.md`](er_diagram.md) contains the Mermaid source.
- [`er_diagram.svg`](er_diagram.svg) is the rendered diagram export.
- [`er_diagram.png`](er_diagram.png) is the raster preview.
