# HBnB Evolution — Part 4: Simple Web Client

Part 4 adds a front-end web client built with HTML5, CSS3, and JavaScript ES6
on top of the authenticated HBnB REST API. The client talks to the API with
the Fetch API, stores the JWT session token in a cookie, and updates the pages
dynamically without reloads. The API is implemented with Flask, Flask-RESTX,
JWT, bcrypt, and SQLAlchemy, and manages users, amenities, places, and reviews
through a layered API → Facade → Repository architecture.

## Web client

- `index.html` — lists all places as cards with a client-side max-price
  filter (10 / 50 / 100 / All). The login link is shown only when the user is
  not authenticated.
- `login.html` — email/password form. A successful login stores the JWT in a
  `token` cookie and redirects to the index page; a failed login shows an
  error message.
- `place.html?id=<place_id>` — detailed view of a place (host, price,
  description, amenities) and its reviews with reviewer name and rating. The
  "Add a Review" action is visible only to authenticated users.
- `add_review.html?id=<place_id>` — review form (text and 1–5 rating).
  Unauthenticated users are redirected to the index page.
- `scripts.js` — all client logic; `styles.css` — all styles; `images/` —
  logo, favicon, and icons.

All pages validate with no errors on the W3C validator.

## Run the API

From this directory:

```bash
pip install -r requirements.txt
python run.py
```

CORS is enabled in the application factory (`flask-cors`) for the
`/api/v1/*` routes so the client can call the API from another origin.

Useful URLs:

- API status: `http://127.0.0.1:5000/`
- Swagger UI: `http://127.0.0.1:5000/api/v1/`
- OpenAPI JSON: `http://127.0.0.1:5000/swagger.json`

The seeded development administrator is:

- Email: `admin@hbnb.io`
- Password: `admin1234`

Set `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL` through environment
variables outside local development.

## Run the client

With the API running, serve this directory over HTTP and open the index page:

```bash
python -m http.server 8000
```

Then browse to `http://localhost:8000/index.html`. Serve the files instead of
opening them directly (`file://`) so cookies and CORS work as intended.

## Main API behavior

- The application factory accepts development, testing, or production
  configuration classes.
- Passwords are hashed with bcrypt and never appear in API responses.
- JWT identity and admin claims control protected operations.
- Users may update only their own names; admins may manage every user.
- Only admins may create or update amenities.
- Only a place owner or an admin may update or delete that place.
- Only a review author or an admin may update or delete that review.
- A user may review a place once and may not review their own place.
- Model and Facade validation enforce valid fields, relationships, and atomic
  updates.
- Each entity uses a dedicated SQLAlchemy repository.

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
