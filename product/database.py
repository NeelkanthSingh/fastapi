from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = 'sqlite:///./product.db'

# database connections(a pool of them) is established through the engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
    "check_same_thread": False
})

# sessionmaker is a factory for creating Session objects, a session is a booking of a database connection through which a transaction is made
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# declarative_base is a base class for all models, it provides functionalities that map models to the database tables and ORM functionalities
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db # yield creates a generator that can be paused and resumed
    finally:
        db.close()