from db import Base
from sqlalchemy import Boolean, Column, Integer, String


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    country = Column(String, nullable=False)
    fullname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "age": self.age,
            "country": self.country,
            "fullname": self.fullname,
        }
