from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    seller_id = Column(Integer, ForeignKey('sellers.id')) # Creates foreigh key relationship, thus a one-to-many relationship.
    seller = relationship("Seller", back_populates='products') # This relationship allows to reach seller from the product row and vice-versa because same is defined down below.

class Seller(Base):
    __tablename__ = 'sellers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    products = relationship("Product", back_populates='seller')
