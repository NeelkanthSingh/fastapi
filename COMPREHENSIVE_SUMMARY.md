# Comprehensive SQLAlchemy & FastAPI Relationships Guide

## Overview

This project demonstrates a complete e-commerce system with all types of database relationships, foreign keys, cascades, and advanced SQLAlchemy features. The system includes products, sellers, categories, inventory, reviews, and users with various relationship types.

## Database Schema Overview

### Core Entities:
- **Product**: Main product entity with relationships to seller, categories, inventory, and reviews
- **Seller**: User who sells products, with profile and follower relationships
- **Category**: Product categories with self-referential hierarchy
- **Inventory**: Stock management for products (one-to-one)
- **Review**: Product reviews with optional user relationship
- **User**: System users who can write reviews
- **SellerProfile**: Extended seller information (one-to-one)

## Relationship Types Demonstrated

### 1. One-to-Many (1:N)
**Example**: Seller → Products
```python
# In Seller model
products = relationship("Product", back_populates='seller', cascade='all, delete-orphan')

# In Product model
seller_id = Column(Integer, ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
seller = relationship("Seller", back_populates='products', lazy='joined')
```

**Key Features:**
- Foreign key with CASCADE delete
- Bidirectional relationship with `back_populates`
- Eager loading with `lazy='joined'`
- Dynamic loading for pagination

### 2. Many-to-One (N:1)
**Example**: Products → Seller
- Reverse of One-to-Many
- Same relationship definition
- Used for filtering and navigation

### 3. One-to-One (1:1)
**Example**: Product ↔ Inventory
```python
# In Product model
inventory = relationship("Inventory", back_populates='product', uselist=False, cascade='all, delete-orphan')

# In Inventory model
product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), unique=True, nullable=False)
product = relationship("Product", back_populates='inventory')
```

**Key Features:**
- `uselist=False` ensures one-to-one relationship
- `unique=True` on foreign key
- `cascade='all, delete-orphan'` for automatic cleanup

### 4. Many-to-Many (N:N)
**Example**: Products ↔ Categories
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
categories = relationship("Category", secondary=product_category, back_populates='products', lazy='selectin')

# In Category model
products = relationship("Product", secondary=product_category, back_populates='categories', lazy='selectin')
```

**Key Features:**
- Association table with additional metadata
- Bidirectional relationship
- Efficient loading with `selectin`

### 5. Self-Referential
**Example**: Category hierarchy
```python
# In Category model
parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
subcategories = relationship("Category", backref=backref('parent', remote_side=[id]), lazy='dynamic')
```

**Key Features:**
- Same table references itself
- `remote_side` for proper relationship direction
- Dynamic loading for large hierarchies

## Foreign Key Cascade Options

### Database-Level Cascades:
- `CASCADE`: Delete related records
- `SET NULL`: Set foreign key to NULL
- `SET DEFAULT`: Set foreign key to default value
- `RESTRICT`: Prevent deletion if related records exist
- `NO ACTION`: Similar to RESTRICT

### SQLAlchemy Cascade Options:
- `save-update`: Save related objects when parent is saved
- `merge`: Merge related objects when parent is merged
- `refresh-expire`: Refresh related objects when parent is refreshed
- `expunge`: Remove related objects from session when parent is expunged
- `delete`: Delete related objects when parent is deleted
- `delete-orphan`: Delete related objects when they're no longer associated
- `all`: All of the above
- `all, delete-orphan`: All cascades plus delete orphaned records

## Lazy Loading Strategies

### Available Options:
1. **`select`** (default): Load when accessed
2. **`joined`**: Load with JOIN in same query
3. **`selectin`**: Load with separate SELECT IN query
4. **`subquery`**: Load with subquery
5. **`dynamic`**: Return query object instead of results
6. **`noload`**: Don't load at all
7. **`raise`**: Raise error if accessed

### Best Practices:
- Use `joined` for frequently accessed relationships
- Use `selectin` for many-to-many relationships
- Use `dynamic` for large collections with filtering
- Use `noload` when you don't need the relationship

## Optional Fields and Relationships

### Making Fields Optional:
```python
# Nullable fields
description = Column(Text, nullable=True)
phone = Column(String(20), nullable=True)

# Optional foreign keys
user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
user = relationship("User", back_populates='reviews')
```

### Handling in FastAPI:
```python
# In Pydantic schemas
class ReviewResponse(BaseModel):
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True
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
```

**Usage:**
- Instance: `product.is_expensive`
- Query: `db.query(Product).filter(Product.is_expensive).all()`

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

### Pydantic Schemas:
- **Base schemas**: For input validation
- **Create schemas**: For POST requests
- **Update schemas**: For PUT/PATCH requests
- **Response schemas**: For GET responses
- **List schemas**: For paginated responses

### API Endpoints:
- **CRUD operations** for all entities
- **Relationship endpoints** for navigating relationships
- **Search and filtering** with multiple criteria
- **Eager loading** to avoid N+1 queries
- **Error handling** with structured responses

### Eager Loading Examples:
```python
# Avoid N+1 queries
products = db.query(Product).options(
    joinedload(Product.seller),
    selectinload(Product.categories)
).all()
```

## Best Practices

### 1. Cascade Strategy:
- Use `delete-orphan` for one-to-one relationships
- Use `save-update` for many-to-many relationships
- Use `CASCADE` foreign keys for dependent data

### 2. Lazy Loading:
- Choose appropriate lazy loading strategy
- Use eager loading to avoid N+1 queries
- Consider query performance implications

### 3. Indexing:
- Index foreign keys
- Index frequently queried fields
- Use composite indexes for common queries

### 4. Constraints:
- Use check constraints for data validation
- Use unique constraints for business rules
- Use foreign key constraints for referential integrity

### 5. Error Handling:
- Handle optional relationships gracefully
- Provide meaningful error messages
- Use structured error responses

### 6. Performance:
- Use appropriate lazy loading
- Implement pagination for large datasets
- Use database indexes effectively
- Monitor query performance

## File Structure

```
FastAPI/
├── main.py                 # FastAPI application entry point
├── create_tables.py        # Database table creation script
├── RELATIONSHIPS_GUIDE.md  # Comprehensive guide
├── COMPREHENSIVE_SUMMARY.md # This summary
├── product/
│   ├── __init__.py
│   ├── database.py         # Database configuration
│   ├── models.py           # SQLAlchemy models with all relationships
│   ├── schemas.py          # Pydantic schemas
│   ├── main.py            # Original API
│   └── api_examples.py    # Comprehensive API examples
├── product.db             # SQLite database file
├── requirements.txt       # Dependencies
└── README.md             # Project documentation
```

## Usage Examples

### Creating Related Data:
```python
# Create seller with products
seller = Seller(name="John Doe", email="john@example.com")
product1 = Product(name="Laptop", price=999.99, seller=seller)
product2 = Product(name="Mouse", price=29.99, seller=seller)
db.add(seller)
db.commit()
```

### Querying Relationships:
```python
# Get seller with all products
seller = db.query(Seller).filter(Seller.id == 1).first()
for product in seller.products:
    print(f"Product: {product.name}")

# Get product with seller info
product = db.query(Product).filter(Product.id == 1).first()
print(f"Seller: {product.seller.name}")
```

### Many-to-Many Operations:
```python
# Add category to product
product.categories.append(category)
db.commit()

# Remove category from product
product.categories.remove(category)
db.commit()
```

### Cascade Operations:
```python
# Delete seller (cascades to products, inventory, reviews)
db.delete(seller)
db.commit()

# Delete product (cascades to inventory, reviews)
db.delete(product)
db.commit()
```

This comprehensive system demonstrates all the essential aspects of database relationships in SQLAlchemy and FastAPI, providing a solid foundation for building complex applications with proper data modeling and API design. 