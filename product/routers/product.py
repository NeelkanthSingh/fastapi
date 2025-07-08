from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import Product, DisplayProduct
from .. import models
from typing import List

router = APIRouter()

# Injection DB session using Depends and cleanup is done after the call finishes, yield ensures of that
# status_code can be added this way
@router.post('/product', status_code=status.HTTP_201_CREATED, tags=["Product"])
def add(product: Product, db: Session = Depends(get_db)):
    new_product = models.Product(name = product.name, description = product.description, price = product.price, seller_id = 1)
    db.add(new_product)
    db.commit()
    db.refresh(new_product) # Updates the Python object with database-generated values. For example, if your table has an auto-incrementing ID, this fills in the ID
    return product


@router.get('/products/{id}', response_model=DisplayProduct, tags=["Product"])
def get_product(id, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        # Need to send the error message this way because the response model is set and its not possible to send message as DisplayProduct response model
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get('/products', response_model=List[DisplayProduct], tags=["Product"])
def get_products(response: Response, db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products

@router.put('/products/{id}', tags=["Product"])
def update(id, request: Product, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id)
    if product.first():
        product.update(request.dict())
        db.commit()
        return {'message': "Product updated successfully!!"}
    else:
        return {'message': "Product not found!!"}

@router.delete('/product/{id}', tags=["Product"])
def delete(id, db: Session = Depends(get_db)):
    # Does not synchronize all the ojects in the current session to reflect the deletion.
    db.query(models.Product).filter(models.Product.id == id).delete(synchronize_session=False) 
    db.commit()

    all_products = db.query(models.Product).all()

    for product in all_products:
        print(product.id)
    return {'message': f'Product with id = {id}, is now deleted'}