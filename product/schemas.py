from pydantic import BaseModel

class Product(BaseModel):
    name: str
    description: str
    price: int

class Seller(BaseModel):
    name: str
    email: str
    password: str

class DisplaySeller(BaseModel):
    name: str
    email: str
    class Config:
        from_attributes = True

class DisplayProduct(BaseModel):
    name: str
    description: str
    seller_id: DisplaySeller
    
    class Config:
        from_attributes = True # allows conversion of sqlalchemy object to pydantic object, they must share same name and compatible type.