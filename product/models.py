from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DateTime, 
    Text, Float, UniqueConstraint, Index, CheckConstraint,
    Table, MetaData
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base
import uuid
from datetime import datetime

# Association table for many-to-many relationship
product_category = Table(
    'product_category',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

class Product(Base):
    """
    Product model demonstrating various relationship types and advanced features
    """
    __tablename__ = 'products'
    
    # Primary key with UUID (PostgreSQL specific, but shown for completeness)
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Standard primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic fields with constraints
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)  # Optional field
    price = Column(Float, nullable=False, index=True)
    
    # Foreign key with cascade options
    seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
    
    # One-to-Many: Product belongs to one Seller
    seller = relationship("Seller", back_populates='products', lazy='joined')
    
    # Many-to-Many: Product can have multiple categories
    categories = relationship(
        "Category", 
        secondary=product_category,
        back_populates='products',
        lazy='selectin'  # Load categories when product is loaded
    )
    
    # One-to-One: Product has one inventory record
    inventory = relationship("Inventory", back_populates='product', uselist=False, cascade='all, delete-orphan')
    
    # One-to-Many: Product can have multiple reviews
    reviews = relationship("Review", back_populates='product', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Status field with check constraint
    status = Column(String(20), default='active', nullable=False)
    
    # JSON field for flexible data (PostgreSQL specific)
    # metadata = Column(JSONB, nullable=True)
    
    # Array field (PostgreSQL specific)
    # tags = Column(ARRAY(String), nullable=True)
    
    # Hybrid property example
    @hybrid_property
    def is_expensive(self):
        return self.price > 100
    
    @is_expensive.expression
    def is_expensive(cls):
        return cls.price > 100
    
    # Composite index
    __table_args__ = (
        Index('idx_product_seller_status', 'seller_id', 'status'),
        Index('idx_product_price_name', 'price', 'name'),
        UniqueConstraint('name', 'seller_id', name='uq_product_name_seller'),
        CheckConstraint('price >= 0', name='check_positive_price'),
        CheckConstraint("status IN ('active', 'inactive', 'draft')", name='check_valid_status')
    )

class Seller(Base):
    """
    Seller model with one-to-many relationship to products
    """
    __tablename__ = 'sellers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    
    # Optional fields
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # One-to-Many: Seller has many products
    products = relationship(
        "Product", 
        back_populates='seller',
        cascade='all, delete-orphan',  # Delete products when seller is deleted
        lazy='dynamic'  # Return query object instead of list
    )
    
    # One-to-One: Seller has one profile
    profile = relationship("SellerProfile", back_populates='seller', uselist=False, cascade='all, delete-orphan')
    
    # Many-to-Many: Seller can follow other sellers
    following = relationship(
        'Seller',
        secondary='seller_followers',
        primaryjoin='Seller.id == seller_followers.c.follower_id',
        secondaryjoin='Seller.id == seller_followers.c.following_id',
        backref=backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_seller_email_name', 'email', 'name'),
    )

# Association table for seller followers (many-to-many)
seller_followers = Table(
    'seller_followers',
    Base.metadata,
    Column('follower_id', Integer, ForeignKey('sellers.id', ondelete='CASCADE'), primary_key=True),
    Column('following_id', Integer, ForeignKey('sellers.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

class Category(Base):
    """
    Category model for many-to-many relationship with products
    """
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Many-to-Many: Category can have multiple products
    products = relationship(
        "Product",
        secondary=product_category,
        back_populates='categories',
        lazy='selectin'
    )
    
    # Self-referential relationship: Categories can have subcategories
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    subcategories = relationship(
        "Category",
        backref=backref('parent', remote_side=[id]),
        lazy='dynamic'
    )

class Inventory(Base):
    """
    Inventory model demonstrating one-to-one relationship
    """
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), unique=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=10, nullable=False)
    
    # One-to-One: Inventory belongs to one product
    product = relationship("Product", back_populates='inventory')
    
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_positive_quantity'),
        CheckConstraint('reorder_level >= 0', name='check_positive_reorder_level'),
    )

class Review(Base):
    """
    Review model demonstrating one-to-many relationship with cascade options
    """
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # Optional foreign key
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    
    # One-to-Many: Review belongs to one product
    product = relationship("Product", back_populates='reviews')
    
    # Optional relationship to user
    user = relationship("User", back_populates='reviews')
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        Index('idx_review_product_rating', 'product_id', 'rating'),
    )

class User(Base):
    """
    User model for reviews
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # One-to-Many: User can have multiple reviews
    reviews = relationship("Review", back_populates='user', cascade='all, delete-orphan')
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

class SellerProfile(Base):
    """
    SellerProfile model demonstrating one-to-one relationship
    """
    __tablename__ = 'seller_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='CASCADE'), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    social_media = Column(Text, nullable=True)  # JSON string or use JSONB for PostgreSQL
    
    # One-to-One: Profile belongs to one seller
    seller = relationship("Seller", back_populates='profile')
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)