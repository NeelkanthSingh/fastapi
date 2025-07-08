from fastapi import FastAPI
from typing import List
from .import models
from .database import engine
from .routers import product, seller

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

app.include_router(seller.router)
app.include_router(product.router)

models.Base.metadata.create_all(engine)


