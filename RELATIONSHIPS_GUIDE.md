# SQLAlchemy & FastAPI Relationships Comprehensive Guide

## Table of Contents
1. [Foreign Keys](#foreign-keys)
2. [Relationship Types](#relationship-types)
3. [Cascade Options](#cascade-options)
4. [Lazy Loading Strategies](#lazy-loading-strategies)
5. [Optional Fields](#optional-fields)
6. [Indexes and Constraints](#indexes-and-constraints)
7. [Advanced Features](#advanced-features)
8. [FastAPI Integration](#fastapi-integration)
9. [Best Practices](#best-practices)

## Foreign Keys

### Basic Foreign Key
```python
# Simple foreign key
seller_id = Column(Integer, ForeignKey('sellers.id'), nullable=False)
```

### Foreign Key with Cascade Options
```python
# Cascade delete - when seller is deleted, all products are deleted
seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)

# Set NULL - when user is deleted, review.user_id becomes NULL
user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
```

### Available Cascade Options:
- `CASCADE`: Delete related records
- `SET NULL`: Set foreign key to NULL
- `SET DEFAULT`: Set foreign key to default value
- `RESTRICT`: Prevent deletion if related records exist
- `NO ACTION`: Similar to RESTRICT

## Relationship Types

### 1. One-to-Many (1:N)
**Example**: One Seller has many Products

```python
# In Seller model
products = relationship("Product", back_populates='seller', cascade='all, delete-orphan')

# In Product model
seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
seller = relationship("Seller", back_populates='products', lazy='joined')
```

**Usage in FastAPI:**
```python
# Get seller with all products
seller = db.query(Seller).filter(Seller.id == seller_id).first()
for product in seller.products:
    print(f"Product: {product.name}")

# Get product with seller info
product = db.query(Product).filter(Product.id == product_id).first()
print(f"Seller: {product.seller.name}")
```

### 2. Many-to-One (N:1)
**Example**: Many Products belong to one Seller

This is the reverse of One-to-Many, using the same relationship definition.

### 3. One-to-One (1:1)
**Example**: One Product has one Inventory record

```python
# In Product model
inventory = relationship("Inventory", back_populates='product', uselist=False, cascade='all, delete-orphan')

# In Inventory model
product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), unique=True, nullable=False)
product = relationship("Product", back_populates='inventory')
```

**Key points:**
- Use `uselist=False` to ensure one-to-one relationship
- Add `unique=True` to the foreign key column
- Use `cascade='all, delete-orphan'` to delete related record when parent is deleted

### 4. Many-to-Many (N:N)
**Example**: Products can have multiple Categories, Categories can have multiple Products

```python
# Association table
product_category = Table(
    'product_category',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

# In Product model
categories = relationship(
    "Category", 
    secondary=product_category,
    back_populates='products',
    lazy='selectin'
)

# In Category model
products = relationship(
    "Product",
    secondary=product_category,
    back_populates='categories',
    lazy='selectin'
)
```

**Usage in FastAPI:**
```python
# Add category to product
product = db.query(Product).filter(Product.id == product_id).first()
category = db.query(Category).filter(Category.id == category_id).first()
product.categories.append(category)
db.commit()

# Get all categories for a product
product = db.query(Product).filter(Product.id == product_id).first()
for category in product.categories:
    print(f"Category: {category.name}")

# Get all products in a category
category = db.query(Category).filter(Category.id == category_id).first()
for product in category.products:
    print(f"Product: {product.name}")
```

### 5. Self-Referential Relationships
**Example**: Categories can have subcategories

```python
# In Category model
parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
subcategories = relationship(
    "Category",
    backref=backref('parent', remote_side=[id]),
    lazy='dynamic'
)
```

## Cascade Options

### Available Cascade Options:
- `save-update`: Save related objects when parent is saved
- `merge`: Merge related objects when parent is merged
- `refresh-expire`: Refresh related objects when parent is refreshed
- `expunge`: Remove related objects from session when parent is expunged
- `delete`: Delete related objects when parent is deleted
- `delete-orphan`: Delete related objects when they're no longer associated
- `all`: All of the above
- `all, delete-orphan`: All cascades plus delete orphaned records

### Common Cascade Patterns:
```python
# Delete products when seller is deleted
products = relationship("Product", cascade='all, delete-orphan')

# Don't cascade deletes (default)
products = relationship("Product", cascade='save-update')

# Full cascade
profile = relationship("SellerProfile", cascade='all, delete-orphan')
```

## Lazy Loading Strategies

### Available Lazy Options:
- `select`: Load when accessed (default)
- `joined`: Load with JOIN in same query
- `selectin`: Load with separate SELECT IN query
- `subquery`: Load with subquery
- `dynamic`: Return query object instead of results
- `noload`: Don't load at all
- `raise`: Raise error if accessed

### Examples:
```python
# Eager loading - load seller with product
seller = relationship("Seller", back_populates='products', lazy='joined')

# Lazy loading - load when accessed
categories = relationship("Category", lazy='select')

# Dynamic loading - return query object
products = relationship("Product", lazy='dynamic')

# Usage with dynamic loading
seller = db.query(Seller).filter(Seller.id == seller_id).first()
expensive_products = seller.products.filter(Product.price > 100).all()
```

## Optional Fields

### Making Fields Optional:
```python
# Nullable fields
description = Column(Text, nullable=True)
phone = Column(String(20), nullable=True)
address = Column(Text, nullable=True)

# Optional foreign keys
user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
user = relationship("User", back_populates='reviews')
```

### Handling Optional Relationships in FastAPI:
```python
# In Pydantic schemas
class ReviewResponse(BaseModel):
    id: int
    rating: int
    comment: Optional[str] = None
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# In API endpoint
@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
```

## Indexes and Constraints

### Single Column Indexes:
```python
name = Column(String(100), nullable=False, index=True)
email = Column(String(255), nullable=False, unique=True, index=True)
```

### Composite Indexes:
```python
__table_args__ = (
    Index('idx_product_seller_status', 'seller_id', 'status'),
    Index('idx_product_price_name', 'price', 'name'),
)
```

### Unique Constraints:
```python
__table_args__ = (
    UniqueConstraint('name', 'seller_id', name='uq_product_name_seller'),
)
```

### Check Constraints:
```python
__table_args__ = (
    CheckConstraint('price >= 0', name='check_positive_price'),
    CheckConstraint("status IN ('active', 'inactive', 'draft')", name='check_valid_status'),
    CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
)
```

## Advanced Features

### Hybrid Properties:
```python
@hybrid_property
def is_expensive(self):
    return self.price > 100

@is_expensive.expression
def is_expensive(cls):
    return cls.price > 100

# Usage
product = db.query(Product).filter(Product.id == product_id).first()
if product.is_expensive:  # Python property
    print("This is expensive")

# Database query
expensive_products = db.query(Product).filter(Product.is_expensive).all()
```

### Timestamps:
```python
created_at = Column(DateTime, default=func.now(), nullable=False)
updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

### PostgreSQL-Specific Features:
```python
# UUID primary key
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# JSON field
metadata = Column(JSONB, nullable=True)

# Array field
tags = Column(ARRAY(String), nullable=True)
```

## FastAPI Integration

### Pydantic Schemas with Relationships:
```python
from pydantic import BaseModel
from typing import Optional, List

class CategoryResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class SellerResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    seller: SellerResponse
    categories: List[CategoryResponse]
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    seller_id: int
    category_ids: List[int] = []
```

### API Endpoints with Relationships:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Create product
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        seller_id=product.seller_id
    )
    
    # Add categories
    if product.category_ids:
        categories = db.query(Category).filter(Category.id.in_(product.category_ids)).all()
        db_product.categories = categories
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/sellers/{seller_id}/products", response_model=List[ProductResponse])
def get_seller_products(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller.products.all()
```

### Eager Loading in API Endpoints:
```python
@router.get("/products/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    # Eager load relationships to avoid N+1 queries
    products = db.query(Product).options(
        joinedload(Product.seller),
        joinedload(Product.categories)
    ).offset(skip).limit(limit).all()
    return products
```

## Best Practices

### 1. Use Appropriate Cascade Options
```python
# Use delete-orphan for one-to-one relationships
profile = relationship("SellerProfile", cascade='all, delete-orphan')

# Use save-update for many-to-many relationships
categories = relationship("Category", secondary=product_category)
```

### 2. Choose Right Lazy Loading Strategy
```python
# Use 'joined' for frequently accessed relationships
seller = relationship("Seller", lazy='joined')

# Use 'dynamic' for large collections
products = relationship("Product", lazy='dynamic')

# Use 'selectin' for many-to-many relationships
categories = relationship("Category", lazy='selectin')
```

### 3. Add Proper Indexes
```python
# Index foreign keys
seller_id = Column(Integer, ForeignKey('sellers.id'), nullable=False, index=True)

# Index frequently queried fields
email = Column(String(255), nullable=False, unique=True, index=True)

# Composite indexes for common queries
__table_args__ = (
    Index('idx_product_seller_status', 'seller_id', 'status'),
)
```

### 4. Use Constraints for Data Integrity
```python
__table_args__ = (
    CheckConstraint('price >= 0', name='check_positive_price'),
    UniqueConstraint('name', 'seller_id', name='uq_product_name_seller'),
)
```

### 5. Handle Optional Relationships Gracefully
```python
# In Pydantic schemas
class ReviewResponse(BaseModel):
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# In API endpoints
if review.user:
    user_data = UserResponse.from_orm(review.user)
else:
    user_data = None
```

### 6. Use Eager Loading to Avoid N+1 Queries
```python
# Bad: N+1 queries
products = db.query(Product).all()
for product in products:
    print(product.seller.name)  # New query for each product

# Good: Single query with JOIN
products = db.query(Product).options(joinedload(Product.seller)).all()
for product in products:
    print(product.seller.name)  # No additional queries
```

This comprehensive guide covers all the essential aspects of relationships in SQLAlchemy and FastAPI, from basic foreign keys to advanced features like hybrid properties and PostgreSQL-specific data types. 