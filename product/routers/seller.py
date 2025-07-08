from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models
from ..schemas import Seller, DisplaySeller
from ..database import get_db
from passlib.context import CryptContext

router = APIRouter()

# This is a password hashing manager from the passlib library
pwd_context = CryptContext(schemes=['bcrypt'], deprecated = "auto") # where bcrypt is industry standard hashing algorithm, deprecated = "auto" automatically handles deprecated hashing schemes.

@router.post('/seller', response_model=DisplaySeller, tags=["Seller"])
def add_seller(request: Seller, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(request.password)
    new_seller = models.Seller(name = request.name, email = request.email, password = hashed_password)
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)

    return new_seller
