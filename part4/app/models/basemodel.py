"""Shared SQLAlchemy base model."""

import uuid
from datetime import datetime, timezone

from extention import db


def utcnow():
    """Return naive UTC for SQLAlchemy DateTime compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseModel(db.Model):
    """Abstract base containing identifiers, timestamps, and safe updates."""

    __abstract__ = True

    id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", str(uuid.uuid4()))
        now = utcnow()
        self.created_at = kwargs.pop("created_at", now)
        self.updated_at = kwargs.pop("updated_at", now)
        super().__init__(**kwargs)

    def save(self):
        self.updated_at = utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def update(self, data):
        """Validate an update and restore the object if validation fails."""
        protected = {"id", "created_at", "updated_at"}
        if protected.intersection(data):
            raise ValueError("id and timestamps cannot be modified")

        previous = {key: getattr(self, key, None) for key in data}
        try:
            for key, value in data.items():
                if not hasattr(type(self), key) and not hasattr(self, key):
                    raise ValueError(f"Unknown attribute: {key}")
                setattr(self, key, value)
            validate = getattr(self, "validate", None)
            if validate:
                validate()
        except (TypeError, ValueError):
            for key, value in previous.items():
                setattr(self, key, value)
            raise

        self.save()
        return self
