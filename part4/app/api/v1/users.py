"""User API endpoints."""

from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.services import facade


api = Namespace("users", description="User operations")

user_model = api.model("UserCreate", {
    "first_name": fields.String(required=True, description="First name"),
    "last_name": fields.String(required=True, description="Last name"),
    "email": fields.String(required=True, description="Email address"),
    "password": fields.String(required=True, description="Password"),
    "is_admin": fields.Boolean(description="Whether the user is an admin"),
})

user_update_model = api.model("UserUpdate", {
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email address (admin only)"),
    "password": fields.String(description="New password (admin only)"),
    "is_admin": fields.Boolean(description="Admin status (admin only)"),
})

user_response_model = api.model("UserResponse", {
    "id": fields.String(description="User ID"),
    "first_name": fields.String(description="First name"),
    "last_name": fields.String(description="Last name"),
    "email": fields.String(description="Email address"),
    "is_admin": fields.Boolean(description="Whether the user is an admin"),
})


def serialize_user(user):
    """Return public user data; passwords are never serialized."""
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_admin": user.is_admin,
    }


@api.route("/")
class UserList(Resource):
    @jwt_required()
    @api.expect(user_model, validate=True)
    @api.response(201, "User successfully created", user_response_model)
    @api.response(400, "Invalid input data")
    @api.response(403, "Admin privileges required")
    def post(self):
        """Create a user (admin only)."""
        if not get_jwt().get("is_admin", False):
            return {"error": "Admin privileges required"}, 403
        try:
            user = facade.create_user(api.payload or {})
            return serialize_user(user), 201
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400

    @api.response(200, "Users retrieved successfully", [user_response_model])
    def get(self):
        """List all users."""
        return [serialize_user(user) for user in facade.get_alluser()], 200


@api.route("/<user_id>")
class UserResource(Resource):
    @api.response(200, "User retrieved successfully", user_response_model)
    @api.response(404, "User not found")
    def get(self, user_id):
        """Get a user by ID."""
        user = facade.get_user(user_id)
        if not user:
            return {"error": "User not found"}, 404
        return serialize_user(user), 200

    @jwt_required()
    @api.expect(user_update_model, validate=True)
    @api.response(200, "User updated successfully", user_response_model)
    @api.response(400, "Invalid or restricted fields")
    @api.response(403, "Unauthorized action")
    @api.response(404, "User not found")
    def put(self, user_id):
        """Update one's profile, or any profile when acting as admin."""
        user = facade.get_user(user_id)
        if not user:
            return {"error": "User not found"}, 404

        is_admin = get_jwt().get("is_admin", False)
        if get_jwt_identity() != user_id and not is_admin:
            return {"error": "Unauthorized action"}, 403

        data = api.payload or {}
        if not is_admin and {"email", "password", "is_admin"}.intersection(data):
            return {"error": "You cannot modify email or password"}, 400

        try:
            updated = facade.update_user(user_id, data)
            return serialize_user(updated), 200
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400
