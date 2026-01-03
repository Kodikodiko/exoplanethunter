from app.database import engine, Base
from app.models import Star, Planet, ObservationWindow
import os

def reset():
    print("Connecting to database...")
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("Database schema recreated successfully.")

if __name__ == "__main__":
    reset()