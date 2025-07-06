from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Base schemas for basic data
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class SellerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    status: str = Field(default='active', regex='^(active|inactive|draft)$')

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class InventoryBase(BaseModel):
    quantity: int = Field(..., ge=0)
    reorder_level: int = Field(default=10, ge=0)

class SellerProfileBase(BaseModel):
    bio: Optional[str] = None
    website: Optional[str] = Field(None, regex=r'^https?://.*')
    social_media: Optional[str] = None

# Create schemas (for POST requests)
class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None

class SellerCreate(SellerBase):
    password: str = Field(..., min_length=8)

class ProductCreate(ProductBase):
    seller_id: int
    category_ids: List[int] = []

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class ReviewCreate(ReviewBase):
    product_id: int
    user_id: Optional[int] = None

class InventoryCreate(InventoryBase):
    product_id: int

class SellerProfileCreate(SellerProfileBase):
    seller_id: int

# Update schemas (for PUT/PATCH requests)
class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None

class SellerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    status: Optional[str] = Field(None, regex='^(active|inactive|draft)$')
    category_ids: Optional[List[int]] = None

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)

class SellerProfileUpdate(BaseModel):
    bio: Optional[str] = None
    website: Optional[str] = Field(None, regex=r'^https?://.*')
    social_media: Optional[str] = None

# Response schemas (for GET requests)
class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SellerResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class SellerProfileResponse(SellerProfileBase):
    id: int
    seller_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class InventoryResponse(InventoryBase):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True

class ReviewResponse(ReviewBase):
    id: int
    product_id: int
    user_id: Optional[int]
    user: Optional[UserResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: int
    seller_id: int
    seller: SellerResponse
    categories: List[CategoryResponse]
    inventory: Optional[InventoryResponse]
    reviews: List[ReviewResponse]
    created_at: datetime
    updated_at: datetime
    
    @validator('is_expensive', always=True)
    def calculate_is_expensive(cls, v, values):
        return values.get('price', 0) > 100
    
    class Config:
        from_attributes = True

# Detailed response schemas with nested relationships
class ProductDetailResponse(ProductResponse):
    seller: SellerResponse
    categories: List[CategoryResponse]
    inventory: Optional[InventoryResponse]
    reviews: List[ReviewResponse]
    
    class Config:
        from_attributes = True

class SellerDetailResponse(SellerResponse):
    profile: Optional[SellerProfileResponse]
    products: List[ProductResponse]
    
    class Config:
        from_attributes = True

class CategoryDetailResponse(CategoryResponse):
    parent: Optional[CategoryResponse]
    subcategories: List[CategoryResponse]
    products: List[ProductResponse]
    
    class Config:
        from_attributes = True

# List response schemas
class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int

class SellerListResponse(BaseModel):
    items: List[SellerResponse]
    total: int
    page: int
    size: int
    pages: int

class CategoryListResponse(BaseModel):
    items: List[CategoryResponse]
    total: int
    page: int
    size: int
    pages: int

# Specialized schemas for specific use cases
class ProductWithInventoryResponse(ProductResponse):
    inventory: InventoryResponse
    
    class Config:
        from_attributes = True

class ProductWithReviewsResponse(ProductResponse):
    reviews: List[ReviewResponse]
    average_rating: Optional[float] = None
    review_count: int = 0
    
    @validator('average_rating', always=True)
    def calculate_average_rating(cls, v, values):
        reviews = values.get('reviews', [])
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)
    
    @validator('review_count', always=True)
    def calculate_review_count(cls, v, values):
        return len(values.get('reviews', []))
    
    class Config:
        from_attributes = True

# Search and filter schemas
class ProductSearchParams(BaseModel):
    name: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    seller_id: Optional[int] = None
    category_ids: Optional[List[int]] = None
    status: Optional[str] = None
    is_expensive: Optional[bool] = None

class SellerSearchParams(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    has_products: Optional[bool] = None

# Authentication schemas
class SellerLogin(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Error response schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    field: Optional[str] = None

class ValidationErrorResponse(BaseModel):
    detail: List[dict]
    error_code: str = "VALIDATION_ERROR"