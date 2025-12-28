from app.database import SessionLocal as PGSession
from app.models import Base, Star, Planet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def export_to_sqlite():
    print("Connecting to PostgreSQL (Source)...")
    pg_db = PGSession()
    
    print("Reading data...")
    stars = pg_db.query(Star).all()
    planets = pg_db.query(Planet).all()
    print(f"Loaded {len(stars)} stars and {len(planets)} planets.")
    
    pg_db.close()
    
    db_file = "exoplanets.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    print(f"Creating {db_file} (Target)...")
    sqlite_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sqlite_engine)
    
    SessionSQLite = sessionmaker(bind=sqlite_engine)
    sq_db = SessionSQLite()
    
    print("Migrating Stars...")
    # Detach objects from PG session and add to SQLite session
    # We need to create new instances to avoid session attachment issues
    
    # Map old IDs to new objects to maintain relationships if needed
    # But since we copy everything, we can just copy properties.
    # Be careful with foreign keys. 
    # Simplest: Insert Stars first, flush, then Planets.
    
    # Actually, we can just use `make_transient` but creates new instances is safer.
    
    star_map = {} # old_id -> new_star_obj
    
    for s in stars:
        new_star = Star(
            name=s.name,
            ra=s.ra,
            dec=s.dec,
            mag_v=s.mag_v,
            teff=s.teff
        )
        # We assume ID auto-increment in SQLite, so we rely on name matching or just re-linking.
        # However, planets link by `star_id`. 
        # If we let SQLite generate IDs, they might differ.
        # We should explicitly set ID if possible, or re-map.
        # SQLAlchemy usually allows setting ID on insert.
        new_star.id = s.id 
        sq_db.add(new_star)
    
    sq_db.commit()
    
    print("Migrating Planets...")
    for p in planets:
        new_planet = Planet(
            id=p.id,
            name=p.name,
            star_id=p.star_id, # This works because we preserved Star IDs
            period=p.period,
            t0=p.t0,
            duration=p.duration,
            depth_mmag=p.depth_mmag,
            priority=p.priority
        )
        sq_db.add(new_planet)
        
    sq_db.commit()
    sq_db.close()
    print("Export complete.")

if __name__ == "__main__":
    export_to_sqlite()
