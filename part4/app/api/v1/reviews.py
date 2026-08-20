"""Review API endpoints."""

from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade


api = Namespace("reviews", description="Review operations")

review_create_model = api.model("ReviewCreate", {
    "text": fields.String(required=True, description="Review text"),
    "rating": fields.Integer(required=True, description="Rating from 1 to 5"),
    "place_id": fields.String(required=True, description="Place ID"),
    "user_id": fields.String(
        description="Reviewer ID; defaults to the authenticated user"
    ),
})
review_update_model = api.model("ReviewUpdate", {
    "text": fields.String(description="Review text"),
    "rating": fields.Integer(description="Rating from 1 to 5"),
})
review_response_model = api.model("ReviewResponse", {
    "id": fields.String(description="Review ID"),
    "text": fields.String(description="Review text"),
    "rating": fields.Integer(description="Rating from 1 to 5"),
    "user_id": fields.String(description="Reviewer ID"),
    "place_id": fields.String(description="Place ID"),
    "created_at": fields.String(description="Creation timestamp"),
    "updated_at": fields.String(description="Last update timestamp"),
})


def serialize_review(review):
    return {
        "id": review.id,
        "text": review.text,
        "rating": review.rating,
        "user_id": review.user_id,
        "place_id": review.place_id,
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }


def can_manage(review):
    return (
        get_jwt().get("is_admin", False)
        or review.user_id == get_jwt_identity()
    )


@api.route("/")
class ReviewList(Resource):
    @jwt_required()
    @api.expect(review_create_model, validate=True)
    @api.response(201, "Review created", review_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Unauthorized action")
    def post(self):
        """Create a review as the authenticated user."""
        data = dict(api.payload or {})
        identity = get_jwt_identity()
        requested_user = data.get("user_id")
        if requested_user and requested_user != identity:
            return {"error": "Unauthorized action"}, 403
        data["user_id"] = identity

        place = facade.get_place(data.get("place_id"))
        if not place:
            return {"error": "User or place not found"}, 400
        if place.owner_id == identity:
            return {"error": "You cannot review your own place"}, 400

        try:
            review = facade.create_review(data)
            return serialize_review(review), 201
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @api.response(200, "Reviews retrieved", [review_response_model])
    def get(self):
        """List reviews."""
        return [
            serialize_review(review) for review in facade.get_all_reviews()
        ], 200


@api.route("/<review_id>")
class ReviewResource(Resource):
    @api.response(200, "Review retrieved", review_response_model)
    @api.response(404, "Review not found")
    def get(self, review_id):
        """Get a review by ID."""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        return serialize_review(review), 200

    @jwt_required()
    @api.expect(review_update_model, validate=True)
    @api.response(200, "Review updated", review_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Unauthorized action")
    @api.response(404, "Review not found")
    def put(self, review_id):
        """Update a review as its author or an admin."""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        if not can_manage(review):
            return {"error": "Unauthorized action"}, 403
        try:
            updated = facade.update_review(review_id, api.payload or {})
            return serialize_review(updated), 200
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @jwt_required()
    @api.response(200, "Review deleted")
    @api.response(403, "Unauthorized action")
    @api.response(404, "Review not found")
    def delete(self, review_id):
        """Delete a review as its author or an admin."""
        review = facade.get_review(review_id)
        if not review:
            return {"error": "Review not found"}, 404
        if not can_manage(review):
            return {"error": "Unauthorized action"}, 403
        facade.delete_review(review_id)
        return {"message": "Review deleted successfully"}, 200
