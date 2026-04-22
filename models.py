from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), nullable=False, default="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    stock = Column(Integer, nullable=False)
<<<<<<< HEAD
    amount = Column(Integer, nullable=False)
=======
    amount = Column(Integer, nullable=False)
>>>>>>> b04b50b8ca3a8d6b8544cae833fe8bb756ca0cc6
