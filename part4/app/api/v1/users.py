"""User endpoints"""


from flask_restx import Namespace, Resource, fields
from app.services import facade
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,get_jwt


api = Namespace('users', description='User operations')

# Define the user model for input validation and documentation
user_model = api.model('User', {
    'first_name': fields.String(required=True, description='First name of the user'),
    'last_name': fields.String(required=True, description='Last name of the user'),
    'email': fields.String(required=True, description='Email of the user'),
    'password': fields.String(required=True, description='password of the user')
})

user_update_model = api.model(
    'UserUpdate',
    {
        'first_name': fields.String(required=True, description='First name of the user'),
        'last_name': fields.String(required=True, description='Last name of the user'),
    },
)


@api.route('/')
class UserList(Resource):
    @api.expect(user_model, validate=True)
    @api.response(201, 'User successfully created')
    @api.response(400, 'Email already registered')
    @api.response(400, 'Invalid input data')
    @jwt_required()
    def post(self):
        """Register a new user"""
        if (get_jwt()["is_admin"] == False):
            return {'error': 'Admin privileges required'}, 403
        user_data = api.payload

        # Simulate email uniqueness check (to be replaced by real validation with persistence)
        existing_user = facade.get_user_by_email(user_data['email'])
        if existing_user:
            return {'error': 'Email already registered'}, 400
        user_data['password'] = facade.password_hash(user_data['password'])
        new_user = facade.create_user(user_data)
        return {'id': new_user.id, 'first_name': new_user.first_name, 'last_name': new_user.last_name, 'email': new_user.email}, 201
    
    @api.response(200, 'users retrives successfully')
    def get(self):
        """Get all users"""
        x = facade.get_alluser()
        users = []
        for i in x:
            obj = {"id":i.id,"first_name": i.first_name,"last_name":i.last_name,"email":i.email}
            users.append(obj)
        return users


@api.route('/<user_id>')
class UserResource(Resource):
    @api.response(200, 'User details retrieved successfully')
    @api.response(404, 'User not found')
    def get(self, user_id):
        """Get user details by ID"""
        user = facade.get_user(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return {'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email}, 200

    @api.expect(user_update_model, validate=True)
    @api.response(200, "User changes successfully")
    @api.response(404, "User Not Found")
    @jwt_required()
    def put(self,user_id):
        """change user data"""
        role = get_jwt()["is_admin"]
        if (api.payload.get("user_id") != get_jwt_identity()):
            return "Unauthorized action", 403
        
        if (api.payload.get("email") != None or api.payload.get("password") != None):
            if (role == False):
                return "You cannot modify email or password", 400
        x = facade.update_user(user_id,api.payload)
        if (x != False):
            return "User changes successfully",201
        else:
            return "User Not Found",404
