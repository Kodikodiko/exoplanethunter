from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Star(Base):
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ra = Column(Float)  # Degrees
    dec = Column(Float) # Degrees
    mag_v = Column(Float, nullable=True)
    teff = Column(Float, nullable=True) # Effective Temperature
    
    planets = relationship("Planet", back_populates="star")

class Planet(Base):
    __tablename__ = "planets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    star_id = Column(Integer, ForeignKey("stars.id"))
    
    # Ephemerides
    period = Column(Float) # Days
    t0 = Column(Float) # BJD_TDB
    duration = Column(Float) # Hours
    depth = Column(Float) # mmag or percent? NASA usually gives percent or ratio. Let's assume mmag for filter, but store what NASA gives.
                          # Agent says "Depth (mmag)" for filter. NASA pscomppars has `pl_trandep` in percent usually.
                          # We will store `depth_mmag`.
    depth_mmag = Column(Float) 
    
    # Uncertainty Data (Errors in Days)
    period_err = Column(Float, nullable=True)
    t0_err = Column(Float, nullable=True)
    
    # Equipment suitability
    min_telescope_in = Column(Float, nullable=True) # Inches
    
    # Exoclock / Priorities
    priority = Column(String, default="Normal") # High, Low, etc.
    
    star = relationship("Star", back_populates="planets")
    observations = relationship("ObservationWindow", back_populates="planet")

class ObservationWindow(Base):
    __tablename__ = "observation_windows"

    id = Column(Integer, primary_key=True, index=True)
    planet_id = Column(Integer, ForeignKey("planets.id"))
    
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    mid_time = Column(DateTime(timezone=True)) # Transit Center
    
    observability_score = Column(Float) # Custom score
    is_visible = Column(Boolean, default=True)
    
    planet = relationship("Planet", back_populates="observations")
