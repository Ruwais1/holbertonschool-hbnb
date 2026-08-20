"""Place API endpoints."""

from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade


api = Namespace("places", description="Place operations")

owner_model = api.model("PlaceOwner", {
    "id": fields.String(description="User ID"),
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email address"),
})
amenity_model = api.model("PlaceAmenity", {
    "id": fields.String(description="Amenity ID"),
    "name": fields.String(description="Amenity name"),
})
place_review_model = api.model("PlaceReview", {
    "id": fields.String(description="Review ID"),
    "text": fields.String(description="Review text"),
    "rating": fields.Integer(description="Rating from 1 to 5"),
    "user_id": fields.String(description="Reviewer ID"),
})

place_request_model = api.model("PlaceCreate", {
    "title": fields.String(required=True, description="Place title"),
    "description": fields.String(description="Place description"),
    "price": fields.Float(required=True, description="Price per night"),
    "latitude": fields.Float(required=True, description="Latitude"),
    "longitude": fields.Float(required=True, description="Longitude"),
    "owner_id": fields.String(
        description="Owner ID; defaults to the authenticated user"
    ),
    "amenities": fields.List(fields.String, description="Amenity IDs"),
})
place_update_model = api.model("PlaceUpdate", {
    "title": fields.String(description="Place title"),
    "description": fields.String(description="Place description"),
    "price": fields.Float(description="Price per night"),
    "latitude": fields.Float(description="Latitude"),
    "longitude": fields.Float(description="Longitude"),
    "amenities": fields.List(fields.String, description="Amenity IDs"),
})
place_response_model = api.model("PlaceResponse", {
    "id": fields.String(description="Place ID"),
    "title": fields.String(description="Place title"),
    "description": fields.String(description="Place description"),
    "price": fields.Float(description="Price per night"),
    "latitude": fields.Float(description="Latitude"),
    "longitude": fields.Float(description="Longitude"),
    "owner": fields.Nested(owner_model),
    "amenities": fields.List(fields.Nested(amenity_model)),
    "reviews": fields.List(fields.Nested(place_review_model)),
    "created_at": fields.String(description="Creation timestamp"),
    "updated_at": fields.String(description="Last update timestamp"),
})


def serialize_place(place):
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
            "email": place.owner.email,
        },
        "amenities": [
            {"id": amenity.id, "name": amenity.name}
            for amenity in place.amenities
        ],
        "reviews": [
            {
                "id": review.id,
                "text": review.text,
                "rating": review.rating,
                "user_id": review.user_id,
            }
            for review in place.reviews
        ],
        "created_at": place.created_at.isoformat(),
        "updated_at": place.updated_at.isoformat(),
    }


def can_manage(place):
    return (
        get_jwt().get("is_admin", False)
        or place.owner_id == get_jwt_identity()
    )


@api.route("/")
class PlaceList(Resource):
    @jwt_required()
    @api.expect(place_request_model, validate=True)
    @api.response(201, "Place created", place_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Unauthorized action")
    def post(self):
        """Create a place owned by the authenticated user."""
        data = dict(api.payload or {})
        identity = get_jwt_identity()
        requested_owner = data.get("owner_id")
        is_admin = get_jwt().get("is_admin", False)
        if requested_owner and requested_owner != identity and not is_admin:
            return {"error": "Unauthorized action"}, 403
        data["owner_id"] = requested_owner if is_admin and requested_owner else identity
        try:
            return serialize_place(facade.create_place(data)), 201
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @api.response(200, "Places retrieved", [place_response_model])
    def get(self):
        """List places."""
        return [serialize_place(place) for place in facade.get_all_places()], 200


@api.route("/<place_id>")
class PlaceResource(Resource):
    @api.response(200, "Place retrieved", place_response_model)
    @api.response(404, "Place not found")
    def get(self, place_id):
        """Get a place by ID."""
        place = facade.get_place(place_id)
        if not place:
            return {"error": "Place not found"}, 404
        return serialize_place(place), 200

    @jwt_required()
    @api.expect(place_update_model, validate=True)
    @api.response(200, "Place updated", place_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Unauthorized action")
    @api.response(404, "Place not found")
    def put(self, place_id):
        """Update a place as its owner or an admin."""
        place = facade.get_place(place_id)
        if not place:
            return {"error": "Place not found"}, 404
        if not can_manage(place):
            return {"error": "Unauthorized action"}, 403
        try:
            updated = facade.update_place(place_id, api.payload or {})
            return serialize_place(updated), 200
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @jwt_required()
    @api.response(200, "Place deleted")
    @api.response(403, "Unauthorized action")
    @api.response(404, "Place not found")
    def delete(self, place_id):
        """Delete a place as its owner or an admin."""
        place = facade.get_place(place_id)
        if not place:
            return {"error": "Place not found"}, 404
        if not can_manage(place):
            return {"error": "Unauthorized action"}, 403
        facade.delete_place(place_id)
        return {"message": "Place deleted successfully"}, 200


@api.route("/<place_id>/reviews")
class PlaceReviewList(Resource):
    @api.response(200, "Reviews retrieved", [place_review_model])
    @api.response(404, "Place not found")
    def get(self, place_id):
        """List reviews for a place."""
        reviews = facade.get_reviews_by_place(place_id)
        if reviews is None:
            return {"error": "Place not found"}, 404
        return [
            {
                "id": review.id,
                "text": review.text,
                "rating": review.rating,
                "user_id": review.user_id,
            }
            for review in reviews
        ], 200
