"""User model."""

import re

from app.models.basemodel import BaseModel
from extention import bcrypt, db


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class User(BaseModel):
    """A registered HBnB user."""

    __tablename__ = "users"

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(
        self, first_name, last_name, email, password, is_admin=False, **kwargs
    ):
        super().__init__(**kwargs)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.validate()

    def validate(self):
        if not isinstance(self.first_name, str) or not self.first_name.strip():
            raise ValueError("first_name must be a non-empty string")
        if len(self.first_name) > 50:
            raise ValueError("first_name must be at most 50 characters")
        if not isinstance(self.last_name, str) or not self.last_name.strip():
            raise ValueError("last_name must be a non-empty string")
        if len(self.last_name) > 50:
            raise ValueError("last_name must be at most 50 characters")
        if not isinstance(self.email, str) or not EMAIL_PATTERN.fullmatch(
            self.email
        ):
            raise ValueError("email must be a valid email")
        if not isinstance(self.password, str) or not self.password.strip():
            raise ValueError("password must be a non-empty string")
        if not isinstance(self.is_admin, bool):
            raise ValueError("is_admin must be a boolean")

    def hash_password(self, password):
        if not isinstance(password, str) or not password.strip():
            raise ValueError("password must be a non-empty string")
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")

    def verify_password(self, password):
        if not isinstance(password, str) or not self.password:
            return False
        return bcrypt.check_password_hash(self.password, password)

    def updateProfile(self, data):
        return self.update(data)
