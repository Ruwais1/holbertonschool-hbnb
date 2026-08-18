"""Module For Users"""
from extention import db
from app.models.basemodel import BaseModel
from extention import bcrypt


# Inherit from BaseModel and db.Model to map this class to a database table
class User(BaseModel, db.Model):
    """User class mapped to the 'users' table"""
    __tablename__ = 'users'

    # SQLAlchemy Columns
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Added **kwargs to gracefully handle SQLAlchemy background initialization
    def __init__(self, first_name, last_name, email, password=None, is_admin=False, **kwargs):
        """Initialization function"""
        super().__init__(**kwargs)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.validate()

    def validate(self):
        """Validate function to ensure all attributes are correct"""
        if not isinstance(self.first_name, str) or self.first_name.strip() == "":
            raise ValueError("first_name must be a non-empty string")

        if len(self.first_name) > 50:
            raise ValueError("first_name must be at most 50 characters")

        if not isinstance(self.last_name, str) or self.last_name.strip() == "":
            raise ValueError("last_name must be a non-empty string")

        if len(self.last_name) > 50:
            raise ValueError("last_name must be at most 50 characters")

        if not isinstance(self.email, str) or self.email.strip() == "":
            raise ValueError("email must be a non-empty string")

        if "@" not in self.email or "." not in self.email:
            raise ValueError("email must be a valid email")

        if not isinstance(self.password, str) or self.password.strip() == "":
            raise ValueError("password must be a non-empty string")

        if not isinstance(self.is_admin, bool):
            raise ValueError("is_admin must be a boolean")

    def updateProfile(self, data):
        """Update user profile data"""
        self.update(data)
        self.validate()
        
    def hash_password(self, password):
        """Hashes the password before storing it."""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        """Verify the provided password against the stored hashed password."""
        return bcrypt.check_password_hash(self.password,password)
    
    
