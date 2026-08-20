"""Persistence repositories for HBnB entities."""

from abc import ABC, abstractmethod

from sqlalchemy.exc import IntegrityError

from extention import db


class Repository(ABC):
    @abstractmethod
    def add(self, obj):
        pass

    @abstractmethod
    def get(self, obj_id):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def update(self, obj_id, data):
        pass

    @abstractmethod
    def delete(self, obj_id):
        pass

    @abstractmethod
    def get_by_attribute(self, attr_name, attr_value):
        pass


class InMemoryRepository(Repository):
    """Small repository retained for isolated unit tests."""

    def __init__(self):
        self._storage = {}

    def add(self, obj):
        self._storage[obj.id] = obj
        return obj

    def get(self, obj_id):
        return self._storage.get(obj_id)

    def get_all(self):
        return list(self._storage.values())

    def update(self, obj_id, data):
        obj = self.get(obj_id)
        if not obj:
            return None
        obj.update(data)
        return obj

    def delete(self, obj_id):
        if obj_id not in self._storage:
            return False
        del self._storage[obj_id]
        return True

    def get_by_attribute(self, attr_name, attr_value):
        return next(
            (
                obj
                for obj in self._storage.values()
                if getattr(obj, attr_name, None) == attr_value
            ),
            None,
        )


class SQLAlchemyRepository(Repository):
    def __init__(self, model):
        self.model = model

    def _commit(self):
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError(
                "A record with these unique values already exists"
            ) from error

    def add(self, obj):
        db.session.add(obj)
        self._commit()
        return obj

    def get(self, obj_id):
        return db.session.get(self.model, obj_id)

    def get_all(self):
        return db.session.execute(db.select(self.model)).scalars().all()

    def update(self, obj_id, data):
        obj = self.get(obj_id)
        if not obj:
            return None
        try:
            obj.update(data)
            self._commit()
        except (TypeError, ValueError):
            db.session.rollback()
            raise
        return obj

    def delete(self, obj_id):
        obj = self.get(obj_id)
        if not obj:
            return False
        db.session.delete(obj)
        self._commit()
        return True

    def get_by_attribute(self, attr_name, attr_value):
        if not hasattr(self.model, attr_name):
            raise ValueError(f"Unknown attribute: {attr_name}")
        statement = db.select(self.model).where(
            getattr(self.model, attr_name) == attr_value
        )
        return db.session.execute(statement).scalar_one_or_none()


class UserRepository(SQLAlchemyRepository):
    def __init__(self):
        from app.models.user import User

        super().__init__(User)

    def get_user_by_email(self, email):
        return self.get_by_attribute("email", email)


class PlaceRepository(SQLAlchemyRepository):
    def __init__(self):
        from app.models.place import Place

        super().__init__(Place)


class ReviewRepository(SQLAlchemyRepository):
    def __init__(self):
        from app.models.review import Review

        super().__init__(Review)

    def get_by_user_and_place(self, user_id, place_id):
        statement = db.select(self.model).where(
            self.model.user_id == user_id,
            self.model.place_id == place_id,
        )
        return db.session.execute(statement).scalar_one_or_none()


class AmenityRepository(SQLAlchemyRepository):
    def __init__(self):
        from app.models.amenity import Amenity

        super().__init__(Amenity)
