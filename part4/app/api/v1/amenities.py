"""Amenity API endpoints."""

from flask_jwt_extended import get_jwt, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade


api = Namespace("amenities", description="Amenity operations")

amenity_model = api.model("AmenityCreate", {
    "name": fields.String(required=True, description="Amenity name")
})
amenity_update_model = api.model("AmenityUpdate", {
    "name": fields.String(description="Amenity name")
})
amenity_response_model = api.model("AmenityResponse", {
    "id": fields.String(description="Amenity ID"),
    "name": fields.String(description="Amenity name"),
})


def serialize_amenity(amenity):
    return {"id": amenity.id, "name": amenity.name}


def admin_required():
    return get_jwt().get("is_admin", False)


@api.route("/")
class AmenityList(Resource):
    @jwt_required()
    @api.expect(amenity_model, validate=True)
    @api.response(201, "Amenity created", amenity_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Admin privileges required")
    def post(self):
        """Create an amenity (admin only)."""
        if not admin_required():
            return {"error": "Admin privileges required"}, 403
        try:
            amenity = facade.create_amenity(api.payload or {})
            return serialize_amenity(amenity), 201
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @api.response(200, "Amenities retrieved", [amenity_response_model])
    def get(self):
        """List amenities."""
        return [
            serialize_amenity(amenity)
            for amenity in facade.get_all_amenities()
        ], 200


@api.route("/<amenity_id>")
class AmenityResource(Resource):
    @api.response(200, "Amenity retrieved", amenity_response_model)
    @api.response(404, "Amenity not found")
    def get(self, amenity_id):
        """Get an amenity by ID."""
        amenity = facade.get_amenity(amenity_id)
        if not amenity:
            return {"error": "Amenity not found"}, 404
        return serialize_amenity(amenity), 200

    @jwt_required()
    @api.expect(amenity_update_model, validate=True)
    @api.response(200, "Amenity updated", amenity_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Admin privileges required")
    @api.response(404, "Amenity not found")
    def put(self, amenity_id):
        """Update an amenity (admin only)."""
        if not admin_required():
            return {"error": "Admin privileges required"}, 403
        try:
            amenity = facade.update_amenity(amenity_id, api.payload or {})
            if not amenity:
                return {"error": "Amenity not found"}, 404
            return serialize_amenity(amenity), 200
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400
