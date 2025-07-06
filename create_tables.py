"""
Database table creation script for the enhanced FastAPI application
"""
from product.database import engine
from product.models import Base

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

def drop_tables():
    """Drop all database tables"""
    print("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
    else:
        create_tables() 