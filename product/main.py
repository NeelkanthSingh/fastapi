from fastapi import FastAPI, Depends, status, Response, HTTPException
from sqlalchemy.orm import Session
from .schemas import Product, DisplayProduct, Seller, DisplaySeller
from typing import List
from .import models
from passlib.context import CryptContext
from .database import engine, SessionLocal

app = FastAPI(
    title="Products API",
    description="Get details for all the products on output",
    terms_of_service="https://www.google.com",
    contact={
        "Developer_name": "Neelkanth Singh",
        "Website": "https://www.google.com",
        "email": "neelkanthsingh.jr@gmail.com"
    },
    license_info={
        "name": "XYZ",
        "url": "https://www.google.com"
    },
    docs_url="/documentation",
    redoc_url=None
)

# This is a password hashing manager from the passlib library
pwd_context = CryptContext(schemes=['bcrypt'], deprecated = "auto") # where bcrypt is industry standard hashing algorithm, deprecated = "auto" automatically handles deprecated hashing schemes.

def get_db():
    db = SessionLocal()
    try:
        yield db # yield creates a generator that can be paused and resumed
    finally:
        db.close()

models.Base.metadata.create_all(engine)

@app.post('/seller', response_model=DisplaySeller, tags=["Seller"])
def add_seller(request: Seller, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(request.password)
    new_seller = models.Seller(name = request.name, email = request.email, password = hashed_password)
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)

    return new_seller

# Injection DB session using Depends and cleanup is done after the call finishes, yield ensures of that
# status_code can be added this way
@app.post('/product', status_code=status.HTTP_201_CREATED, tags=["Product"])
def add(product: Product, db: Session = Depends(get_db)):
    new_product = models.Product(name = product.name, description = product.description, price = product.price, seller_id = 1)
    db.add(new_product)
    db.commit()
    db.refresh(new_product) # Updates the Python object with database-generated values. For example, if your table has an auto-incrementing ID, this fills in the ID
    return product


@app.get('/products/{id}', response_model=DisplayProduct, tags=["Product"])
def get_product(id, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        # Need to send the error message this way because the response model is set and its not possible to send message as DisplayProduct response model
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get('/products', response_model=List[DisplayProduct], tags=["Product"])
def get_products(response: Response, db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products

@app.put('/products/{id}', tags=["Product"])
def update(id, request: Product, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id)
    if product.first():
        product.update(request.dict())
        db.commit()
        return {'message': "Product updated successfully!!"}
    else:
        return {'message': "Product not found!!"}

@app.delete('/product/{id}', tags=["Product"])
def delete(id, db: Session = Depends(get_db)):
    # Does not synchronize all the ojects in the current session to reflect the deletion.
    db.query(models.Product).filter(models.Product.id == id).delete(synchronize_session=False) 
    db.commit()

    all_products = db.query(models.Product).all()

    for product in all_products:
        print(product.id)
    return {'message': f'Product with id = {id}, is now deleted'}