"""review endpoints"""


from flask_restx import Namespace, Resource, fields
from app.services import facade
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,get_jwt


api = Namespace("reviews", "reviews Operations")

def serialize_user(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }

def serialize_place(place):
    return {
        "id": place.id,
        "title": place.title,
    }

def serialize_review(review, include_relations=True):
    """Convert a Review object into a JSON-compatible dictionary."""
    data = {
        "id": review.id,
        "text": review.text,
        "rating": review.rating
    }

    if include_relations:
        data["user_id"] = serialize_user(review.user)
        data["place_id"] = serialize_place(review.place)

    return data

# Define the review model for input validation and documentation
review_model = api.model('Review', {
    'text': fields.String(required=True, description='Text of the review'),
    'rating': fields.Integer(required=True, description='Rating of the place (1-5)'),
    'user_id': fields.String(required=True, description='ID of the user'),
    'place_id': fields.String(required=True, description='ID of the place')
})

@api.route('/')
class ReviewList(Resource):
    @jwt_required()
    @api.expect(review_model)
    @api.response(201, 'Review successfully created')
    @api.response(400, 'Invalid input data')
    def post(self):
        """Register a new review"""
        role = get_jwt()["is_admin"]
        current_user_id = get_jwt_identity()
        place_id = api.payload.get("place_id")
        users_id = api.payload.get("user_id")
        text = api.payload.get("text")
        rating = api.payload.get("rating")
        if (current_user_id != api.payload.get("user_id")):
            return "user id not match with token", 401
        objuser = facade.get_user(users_id)
        objplace = facade.get_place(place_id)
        if (objuser == None or objplace == None):
            return "user or place not found", 404
        if (objplace.owner.id == users_id and role == False):
            return "You cannot review your own place", 400
        
        r = facade.get_all_reviews()
        for review in r:
            if (review.user.id == users_id and review.place.id == place_id):
                return "You have already reviewed this place", 400
        data = {"text":text,"rating":rating,"user":objuser,"place":objplace}
        reviews = facade.create_review(data)
        return serialize_review(reviews),201
        

    @api.response(200, 'List of reviews retrieved successfully')
    def get(self):
        """Retrieve a list of all reviews"""
        # Placeholder for logic to return a list of all reviews
        reviews = facade.get_all_reviews()
        return [
            serialize_review(review, include_relations=True)
            for review in reviews
        ], 200

@api.route('/<review_id>')
class ReviewResource(Resource):
    @api.response(200, 'Review details retrieved successfully')
    @api.response(404, 'Review not found')
    def get(self, review_id):
        """Get review details by ID"""
        rev = facade.get_review(review_id)
        if (rev == None):
            return "review id not found", 404
        return serialize_review(rev)

    @api.expect(review_model)
    @api.response(200, 'Review updated successfully')
    @api.response(404, 'Review not found')
    @api.response(400, 'Invalid input data')
    @jwt_required()
    def put(self, review_id):
        """Update a review's information"""
        if (api.payload.get("user_id") != get_jwt_identity()):
            return "Unauthorized action", 403
        rev = facade.update_review(review_id, api.payload)
        if (rev == False):
            return "Review not found", 404
        return {"message":"review updated successfully"}
    
    @api.response(200, 'Review deleted successfully')
    @api.response(404, 'Review not found')
    @jwt_required()
    def delete(self, review_id):
        """Delete a review"""
        role = get_jwt()["is_admin"]
        if role == False:
            if (api.payload.get("user_id") != get_jwt_identity()):
                return "Unauthorized action", 403
        facade.delete_review(review_id)
        return "Deleted Successfully"
