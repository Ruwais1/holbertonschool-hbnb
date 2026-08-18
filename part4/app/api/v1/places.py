"""Place API endpoints and models."""

from flask_restx import Namespace, Resource, fields
from app.services import facade
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,get_jwt



api = Namespace("places", description="Place operations")


user_model = api.model("PlaceOwner", {
    "id": fields.String(description="User ID"),
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email")
})


amenity_model = api.model("PlaceAmenity", {
    "id": fields.String(description="Amenity ID"),
    "name": fields.String(description="Amenity name")
})


review_model = api.model("PlaceReview", {
    "id": fields.String(description="Review ID"),
    "text": fields.String(description="Text of the review"),
    "rating": fields.Integer(description="Rating of the place (1-5)"),
    "user_id": fields.String(description="ID of the user")
})


place_request_model = api.model("PlaceRequest", {
    "title": fields.String(
        required=True,
        description="Title of the place"
    ),
    "description": fields.String(
        description="Description of the place"
    ),
    "price": fields.Float(
        required=True,
        description="Price per night"
    ),
    "latitude": fields.Float(
        required=True,
        description="Latitude"
    ),
    "longitude": fields.Float(
        required=True,
        description="Longitude"
    ),
    "owner_id": fields.String(
        required=True,
        description="ID of the owner"
    ),
    "amenities": fields.List(
        fields.String,
        description="List of amenity IDs"
    )
})


place_response_model = api.model("PlaceResponse", {
    "id": fields.String(description="Place ID"),
    "title": fields.String(description="Title of the place"),
    "description": fields.String(description="Description of the place"),
    "price": fields.Float(description="Price per night"),
    "latitude": fields.Float(description="Latitude"),
    "longitude": fields.Float(description="Longitude"),
    "owner": fields.Nested(user_model, description="Owner of the place"),
    "amenities": fields.List(
        fields.Nested(amenity_model),
        description="List of amenities"
    ),
    "reviews": fields.List(
        fields.Nested(review_model),
        description="List of reviews"
    )
})


def serialize_place(place):
    """Convert a Place object into a JSON-compatible dictionary."""
    return {
        "id": place.id,
        "title": place.title,
        "description": place.description,
        "price": place.price,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "owner": {
            "id": place.owner.id,
            "first_name": place.owner.first_name,
            "last_name": place.owner.last_name,
            "email": place.owner.email
        },
        "amenities": [
            {
                "id": amenity.id,
                "name": amenity.name
            }
            for amenity in place.amenities
        ],
        "reviews": [
            {
                "id": review.id,
                "text": review.text,
                "rating": review.rating,
                "user_id": review.user.id
            }
            for review in place.reviews
        ]
    }


@api.route("/")
class PlaceList(Resource):
    @jwt_required()
    @api.expect(place_request_model, validate=True)
    @api.response(201, "Place successfully created", place_response_model)
    @api.response(400, "Invalid input data")
    def post(self):
        """Create a new place."""
        try:
            current_user_id = get_jwt_identity()
            if (api.payload.get("owner_id") != current_user_id and not get_jwt()["is_admin"]):
                return {"error": "Unauthorized action"}, 403
            api.payload["owner_id"] = current_user_id
            place = facade.create_place(api.payload or {})
            return serialize_place(place), 201
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @api.response(200, "List of places retrieved successfully")
    def get(self):
        """Retrieve a list of all places."""
        places = facade.get_all_places()
        return [
            serialize_place(place)
            for place in places
        ], 200


@api.route("/<place_id>")
class PlaceResource(Resource):

    @api.response(200, "Place details retrieved successfully", place_response_model)
    @api.response(404, "Place not found")
    def get(self, place_id):
        """Get place details by ID."""
        place = facade.get_place(place_id)

        if not place:
            return {"error": "Place not found"}, 404

        return serialize_place(place), 200

    @api.expect(place_request_model, validate=True)
    @jwt_required()
    @api.response(200, "Place updated successfully", place_response_model)
    @api.response(404, "Place not found")
    @api.response(400, "Invalid input data")
    def put(self, place_id):
        """Update a place."""
        try:
            pl = facade.get_place(place_id)
            if not pl:
                return {"error": "Place not found"}, 404
            if (pl.owner.id != api.payload.get("owner_id") and not get_jwt()["is_admin"]):
                return {"error": "Unauthorized action"}, 403
            place = facade.update_place(place_id, api.payload or {})
            return serialize_place(place), 200
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400


@api.route("/<place_id>/reviews")
class PlaceReviewList(Resource):

    @api.response(
        200,
        "List of reviews for the place retrieved successfully"
    )
    @api.response(404, "Place not found")
    def get(self, place_id):
        """Get all reviews for a specific place."""
        reviews = facade.get_reviews_by_place(place_id)

        if reviews is None:
            return {"error": "Place not found"}, 404

        return [
            {
                "id": review.id,
                "text": review.text,
                "rating": review.rating,
                "user_id": review.user.id
            }
            for review in reviews
        ], 200
