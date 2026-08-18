from app.models.place import Place
from app.models.amenity import Amenity
from app.persistence.repository import SQLAlchemyRepository
from app.models.user import User
from app.models.review import Review
from extention import bcrypt


class HBnBFacade:
    def __init__(self):
        self.user_repo = SQLAlchemyRepository(User)
        self.place_repo = SQLAlchemyRepository(Place)
        self.review_repo = SQLAlchemyRepository(Review)
        self.amenity_repo = SQLAlchemyRepository(Amenity)

    def create_user(self, user_data):
        if (self.get_user_by_email("admin@hbnb.io") is None):
            admin = User(first_name="Admin", last_name="HBnB", email="admin@hbnb.io", password="$2b$12$QU199VJWbC7K/l85EsEPIuWKB/G2omQnt1B.M27jxWxiWaoJwKgiu", is_admin=True)
            self.user_repo.add(admin)
        user = User(**user_data)
        self.user_repo.add(user)
        return user
    
    def get_user(self, user_id):
        return self.user_repo.get(user_id)

    def get_user_by_email(self, email):
        return self.user_repo.get_by_attribute('email', email)

    def get_alluser(self):
        return self.user_repo.get_all()

    def update_user(self, user_id, user_data):
        return self.user_repo.update(user_id, user_data)

    def create_amenity(self, amenity_data):
        amenity = Amenity(**amenity_data)
        self.amenity_repo.add(amenity)
        return amenity

    def get_amenity(self, amenity_id):
        return self.amenity_repo.get(amenity_id)

    def get_all_amenities(self):
        return self.amenity_repo.get_all()

    def update_amenity(self, amenity_id, amenity_data):
        return self.amenity_repo.update(amenity_id, amenity_data)

    def create_place(self, place_data):
        owner_id = place_data.pop("owner_id", None)
        owner = self.get_user(owner_id)

        if not owner:
            raise ValueError("Owner not found")

        amenity_ids = place_data.pop("amenities", [])
        amenities = []

        for amenity_id in amenity_ids:
            amenity = self.get_amenity(amenity_id)
            if not amenity:
                raise ValueError("Amenity not found")
            amenities.append(amenity)

        place = Place(owner=owner, **place_data)

        for amenity in amenities:
            place.add_amenities(amenity)

        self.place_repo.add(place)
        return place

    def get_place(self, place_id):
        return self.place_repo.get(place_id)

    def get_all_places(self):
        return self.place_repo.get_all()

    def get_reviews_by_place(self, place_id):
        place = self.get_place(place_id)
        if not place:
            return None

        return place.reviews

    def update_place(self, place_id, place_data):
        place = self.get_place(place_id)

        if not place:
            return None

        if "owner_id" in place_data:
            owner = self.get_user(place_data.pop("owner_id"))
            if not owner:
                raise ValueError("Owner not found")
            place.owner = owner

        if "amenities" in place_data:
            amenity_ids = place_data.pop("amenities")
            place.amenities = []

            for amenity_id in amenity_ids:
                amenity = self.get_amenity(amenity_id)
                if not amenity:
                    raise ValueError("Amenity not found")
                place.add_amenities(amenity)
                
        if "reviews" in place_data:
            review = place_data.pop("reviews")
            place.reviews.append(review)

        return self.place_repo.update(place_id, place_data)

    def create_review(self, review_data):
        rev = Review(**review_data)
        self.review_repo.add(rev)
        
        if "place" in review_data:
            self.update_place(review_data["place"].id, {"reviews": rev})
            
        return rev

    def get_review(self, review_id):
        return self.review_repo.get(review_id)

    def get_all_reviews(self):
        return self.review_repo.get_all()

    def update_review(self, review_id, review_data):
        return self.review_repo.update(review_id, review_data)

    def delete_review(self, review_id):
        return self.review_repo.delete(review_id)

    def password_hash(self,password):
        return bcrypt.generate_password_hash(password).decode('utf-8')
