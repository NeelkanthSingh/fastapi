"""
Comprehensive FastAPI examples demonstrating all relationship types, cascades, and advanced features
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy import and_, or_, func
from typing import List, Optional
import math

from .database import SessionLocal, engine
from .models import (
    Product, Seller, Category, Inventory, Review, User, SellerProfile,
    product_category, seller_followers
)
from .schemas import (
    # Base schemas
    ProductBase, SellerBase, CategoryBase, UserBase, ReviewBase, InventoryBase,
    # Create schemas
    ProductCreate, SellerCreate, CategoryCreate, UserCreate, ReviewCreate, InventoryCreate,
    # Update schemas
    ProductUpdate, SellerUpdate, CategoryUpdate, UserUpdate, ReviewUpdate, InventoryUpdate,
    # Response schemas
    ProductResponse, SellerResponse, CategoryResponse, UserResponse, ReviewResponse, InventoryResponse,
    ProductDetailResponse, SellerDetailResponse, CategoryDetailResponse,
    # List schemas
    ProductListResponse, SellerListResponse, CategoryListResponse,
    # Specialized schemas
    ProductWithInventoryResponse, ProductWithReviewsResponse,
    # Search schemas
    ProductSearchParams, SellerSearchParams,
    # Error schemas
    ErrorResponse, ValidationErrorResponse
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# ============================================================================
# ONE-TO-MANY RELATIONSHIP EXAMPLES
# ============================================================================

@router.post("/sellers/", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
def create_seller(seller: SellerCreate, db: Session = Depends(get_db)):
    """Create a new seller"""
    # Check if email already exists
    existing_seller = db.query(Seller).filter(Seller.email == seller.email).first()
    if existing_seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_seller = Seller(
        name=seller.name,
        email=seller.email,
        password=seller.password,  # In real app, hash the password
        phone=seller.phone,
        address=seller.address
    )
    db.add(db_seller)
    db.commit()
    db.refresh(db_seller)
    return db_seller

@router.post("/sellers/{seller_id}/products/", response_model=ProductResponse)
def create_product_for_seller(
    seller_id: int, 
    product: ProductCreate, 
    db: Session = Depends(get_db)
):
    """Create a product for a specific seller (One-to-Many)"""
    # Verify seller exists
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Create product
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        status=product.status,
        seller_id=seller_id
    )
    
    # Add categories if provided
    if product.category_ids:
        categories = db.query(Category).filter(Category.id.in_(product.category_ids)).all()
        db_product.categories = categories
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/sellers/{seller_id}/products/", response_model=List[ProductResponse])
def get_seller_products(
    seller_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all products for a seller (One-to-Many)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Use dynamic loading to get products with pagination
    products = seller.products.offset(skip).limit(limit).all()
    return products

@router.get("/sellers/{seller_id}/products/count")
def get_seller_product_count(seller_id: int, db: Session = Depends(get_db)):
    """Get count of products for a seller"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    return {"seller_id": seller_id, "product_count": seller.products.count()}

# ============================================================================
# MANY-TO-ONE RELATIONSHIP EXAMPLES
# ============================================================================

@router.get("/products/{product_id}/seller", response_model=SellerResponse)
def get_product_seller(product_id: int, db: Session = Depends(get_db)):
    """Get the seller of a specific product (Many-to-One)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product.seller

@router.get("/products/", response_model=ProductListResponse)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    seller_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, gt=0),
    max_price: Optional[float] = Query(None, gt=0),
    db: Session = Depends(get_db)
):
    """Get products with optional seller filter (Many-to-One)"""
    query = db.query(Product)
    
    if seller_id:
        query = query.filter(Product.seller_id == seller_id)
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    pages = math.ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

# ============================================================================
# ONE-TO-ONE RELATIONSHIP EXAMPLES
# ============================================================================

@router.post("/products/{product_id}/inventory", response_model=InventoryResponse)
def create_product_inventory(
    product_id: int, 
    inventory: InventoryCreate, 
    db: Session = Depends(get_db)
):
    """Create inventory for a product (One-to-One)"""
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if inventory already exists
    existing_inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if existing_inventory:
        raise HTTPException(status_code=400, detail="Inventory already exists for this product")
    
    db_inventory = Inventory(
        product_id=product_id,
        quantity=inventory.quantity,
        reorder_level=inventory.reorder_level
    )
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@router.get("/products/{product_id}/inventory", response_model=InventoryResponse)
def get_product_inventory(product_id: int, db: Session = Depends(get_db)):
    """Get inventory for a product (One-to-One)"""
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    return inventory

@router.put("/products/{product_id}/inventory", response_model=InventoryResponse)
def update_product_inventory(
    product_id: int, 
    inventory_update: InventoryUpdate, 
    db: Session = Depends(get_db)
):
    """Update inventory for a product (One-to-One)"""
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    # Update fields
    if inventory_update.quantity is not None:
        inventory.quantity = inventory_update.quantity
    if inventory_update.reorder_level is not None:
        inventory.reorder_level = inventory_update.reorder_level
    
    db.commit()
    db.refresh(inventory)
    return inventory

# ============================================================================
# MANY-TO-MANY RELATIONSHIP EXAMPLES
# ============================================================================

@router.post("/categories/", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    # Check if name already exists
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    # Verify parent category exists if provided
    if category.parent_id:
        parent = db.query(Category).filter(Category.id == category.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    db_category = Category(
        name=category.name,
        description=category.description,
        parent_id=category.parent_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.post("/products/{product_id}/categories/{category_id}")
def add_category_to_product(product_id: int, category_id: int, db: Session = Depends(get_db)):
    """Add a category to a product (Many-to-Many)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category is already assigned
    if category in product.categories:
        raise HTTPException(status_code=400, detail="Category already assigned to product")
    
    product.categories.append(category)
    db.commit()
    return {"message": "Category added to product successfully"}

@router.delete("/products/{product_id}/categories/{category_id}")
def remove_category_from_product(product_id: int, category_id: int, db: Session = Depends(get_db)):
    """Remove a category from a product (Many-to-Many)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category not in product.categories:
        raise HTTPException(status_code=400, detail="Category not assigned to product")
    
    product.categories.remove(category)
    db.commit()
    return {"message": "Category removed from product successfully"}

@router.get("/categories/{category_id}/products", response_model=List[ProductResponse])
def get_category_products(category_id: int, db: Session = Depends(get_db)):
    """Get all products in a category (Many-to-Many)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category.products

@router.get("/products/{product_id}/categories", response_model=List[CategoryResponse])
def get_product_categories(product_id: int, db: Session = Depends(get_db)):
    """Get all categories for a product (Many-to-Many)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product.categories

# ============================================================================
# SELF-REFERENTIAL RELATIONSHIP EXAMPLES
# ============================================================================

@router.get("/categories/{category_id}/subcategories", response_model=List[CategoryResponse])
def get_category_subcategories(category_id: int, db: Session = Depends(get_db)):
    """Get subcategories of a category (Self-referential)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category.subcategories.all()

@router.get("/categories/{category_id}/parent", response_model=CategoryResponse)
def get_category_parent(category_id: int, db: Session = Depends(get_db)):
    """Get parent category (Self-referential)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if not category.parent:
        raise HTTPException(status_code=404, detail="Category has no parent")
    
    return category.parent

# ============================================================================
# CASCADE EXAMPLES
# ============================================================================

@router.delete("/sellers/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seller(seller_id: int, db: Session = Depends(get_db)):
    """Delete a seller and all related data (Cascade example)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Due to cascade='all, delete-orphan', this will also delete:
    # - All products (cascade='all, delete-orphan')
    # - Seller profile (cascade='all, delete-orphan')
    # - All inventory records (CASCADE foreign key)
    # - All reviews (CASCADE foreign key)
    db.delete(seller)
    db.commit()
    return None

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product and related data (Cascade example)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Due to cascade='all, delete-orphan', this will also delete:
    # - Inventory record (cascade='all, delete-orphan')
    # - All reviews (cascade='all, delete-orphan')
    # - Category associations (CASCADE in association table)
    db.delete(product)
    db.commit()
    return None

# ============================================================================
# LAZY LOADING EXAMPLES
# ============================================================================

@router.get("/products/{product_id}/detailed", response_model=ProductDetailResponse)
def get_product_detailed(product_id: int, db: Session = Depends(get_db)):
    """Get product with all relationships loaded (Eager loading example)"""
    product = db.query(Product).options(
        joinedload(Product.seller),  # Eager load seller
        selectinload(Product.categories),  # Eager load categories
        selectinload(Product.inventory),  # Eager load inventory
        selectinload(Product.reviews).selectinload(Review.user)  # Eager load reviews and users
    ).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@router.get("/sellers/{seller_id}/detailed", response_model=SellerDetailResponse)
def get_seller_detailed(seller_id: int, db: Session = Depends(get_db)):
    """Get seller with all relationships loaded"""
    seller = db.query(Seller).options(
        selectinload(Seller.profile),
        selectinload(Seller.products).selectinload(Product.categories)
    ).filter(Seller.id == seller_id).first()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    return seller

# ============================================================================
# HYBRID PROPERTY EXAMPLES
# ============================================================================

@router.get("/products/expensive", response_model=List[ProductResponse])
def get_expensive_products(db: Session = Depends(get_db)):
    """Get expensive products using hybrid property"""
    # This uses the hybrid property expression in the database query
    expensive_products = db.query(Product).filter(Product.is_expensive).all()
    return expensive_products

@router.get("/products/{product_id}/price-status")
def get_product_price_status(product_id: int, db: Session = Depends(get_db)):
    """Get product price status using hybrid property"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # This uses the hybrid property on the instance
    return {
        "product_id": product.id,
        "name": product.name,
        "price": product.price,
        "is_expensive": product.is_expensive
    }

# ============================================================================
# ADVANCED QUERY EXAMPLES
# ============================================================================

@router.get("/products/search", response_model=ProductListResponse)
def search_products(
    name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    seller_id: Optional[int] = None,
    category_ids: Optional[List[int]] = None,
    status: Optional[str] = None,
    is_expensive: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Advanced product search with multiple filters"""
    query = db.query(Product)
    
    # Apply filters
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    if seller_id:
        query = query.filter(Product.seller_id == seller_id)
    if status:
        query = query.filter(Product.status == status)
    if is_expensive is not None:
        query = query.filter(Product.is_expensive == is_expensive)
    if category_ids:
        query = query.join(Product.categories).filter(Category.id.in_(category_ids))
    
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    pages = math.ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.get("/sellers/statistics")
def get_seller_statistics(db: Session = Depends(get_db)):
    """Get seller statistics using aggregate functions"""
    stats = db.query(
        func.count(Seller.id).label('total_sellers'),
        func.count(Product.id).label('total_products'),
        func.avg(Product.price).label('average_price'),
        func.max(Product.price).label('max_price'),
        func.min(Product.price).label('min_price')
    ).outerjoin(Seller.products).first()
    
    return {
        "total_sellers": stats.total_sellers,
        "total_products": stats.total_products,
        "average_price": float(stats.average_price) if stats.average_price else 0,
        "max_price": float(stats.max_price) if stats.max_price else 0,
        "min_price": float(stats.min_price) if stats.min_price else 0
    }

# ============================================================================
# OPTIONAL RELATIONSHIP EXAMPLES
# ============================================================================

@router.post("/reviews/", response_model=ReviewResponse)
def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    """Create a review with optional user (Optional relationship)"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == review.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Verify user exists if provided
    if review.user_id:
        user = db.query(User).filter(User.id == review.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    db_review = Review(
        product_id=review.product_id,
        user_id=review.user_id,  # Can be None
        rating=review.rating,
        comment=review.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a review with optional user relationship"""
    review = db.query(Review).options(
        joinedload(Review.user)  # Load user if exists
    ).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review

# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

@router.get("/products/{product_id}/seller", response_model=SellerResponse)
def get_product_seller_with_error_handling(product_id: int, db: Session = Depends(get_db)):
    """Example with comprehensive error handling"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    detail="Product not found",
                    error_code="PRODUCT_NOT_FOUND",
                    field="product_id"
                ).dict()
            )
        
        if not product.seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    detail="Product has no seller",
                    error_code="NO_SELLER",
                    field="seller_id"
                ).dict()
            )
        
        return product.seller
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Internal server error",
                error_code="INTERNAL_ERROR"
            ).dict()
        ) 