from pydantic import BaseModel

class Product(BaseModel):
    name: str
    description: str
    price: int

class DisplayProduct(BaseModel):
    name: str
    description: str
    class Config:
        from_attributes = True # allows conversion of sqlalchemy object to pydantic object, they must share same name and compatible type.