"""Amenity endpoints"""

from flask_restx import Namespace, Resource, fields
from app.services import facade
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,get_jwt


api = Namespace("amenities", description="Amenity operations")

amenity_model = api.model("Amenity", {
    "name": fields.String(required=True, description="Name of the amenity")
})

amenity_update_model = api.model("AmenityUpdate", {
    "name": fields.String(required=False, description="Name of the amenity")
})


@api.route("/")
class AmenityList(Resource):
    @api.expect(amenity_model, validate=True)
    @api.response(201, "Amenity successfully created")
    @api.response(400, "Invalid input data")
    @jwt_required()
    def post(self):
        """Create a new amenity"""
        role = get_jwt()["is_admin"]
        if not role:
            return {"error": "Admin privileges required"}, 403
        try:
            amenity = facade.create_amenity(api.payload)
            return {
                "id": amenity.id,
                "name": amenity.name
            }, 201
        except ValueError as e:
            return {"error": str(e)}, 400

    @api.response(200, "Amenities retrieved successfully")
    def get(self):
        """Get all amenities"""
        amenities = facade.get_all_amenities()
        return [
            {
                "id": amenity.id,
                "name": amenity.name
            }
            for amenity in amenities
        ], 200


@api.route("/<amenity_id>")
class AmenityResource(Resource):
    @api.response(200, "Amenity details retrieved successfully")
    @api.response(404, "Amenity not found")
    def get(self, amenity_id):
        """Get amenity by ID"""
        amenity = facade.get_amenity(amenity_id)
        if not amenity:
            return {"error": "Amenity not found"}, 404

        return {
            "id": amenity.id,
            "name": amenity.name
        }, 200

    @api.expect(amenity_update_model, validate=True)
    @api.response(200, "Amenity updated successfully")
    @api.response(400, "Invalid input data")
    @api.response(404, "Amenity not found")
    @jwt_required()
    def put(self, amenity_id):
        """Update amenity by ID"""
        role = get_jwt()["is_admin"]
        if not role:
            return {"error": "Admin privileges required"}, 403
        try:
            amenity = facade.update_amenity(amenity_id, api.payload)
            if not amenity:
                return {"error": "Amenity not found"}, 404

            return {
                "id": amenity.id,
                "name": amenity.name
            }, 200
        except ValueError as e:
            return {"error": str(e)}, 400
