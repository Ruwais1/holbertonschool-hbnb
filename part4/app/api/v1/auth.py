"""Authentication endpoint."""

from flask_jwt_extended import create_access_token
from flask_restx import Namespace, Resource, fields

from app.services import facade


api = Namespace("auth", description="Authentication operations")

login_model = api.model("Login", {
    "email": fields.String(required=True, description="User email"),
    "password": fields.String(required=True, description="User password"),
})

token_model = api.model("AccessToken", {
    "access_token": fields.String(description="JWT access token")
})


@api.route("/login")
class Login(Resource):
    @api.expect(login_model, validate=True)
    @api.response(200, "Authentication successful", token_model)
    @api.response(401, "Invalid credentials")
    def post(self):
        """Authenticate a user and return a JWT token."""
        credentials = api.payload or {}
        user = facade.get_user_by_email(credentials.get("email"))
        if not user or not user.verify_password(credentials.get("password")):
            return {"error": "Invalid credentials"}, 401
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"is_admin": user.is_admin},
        )
        return {"access_token": token}, 200
