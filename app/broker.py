import requests
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
from app.database import SessionLocal
from app.models import Star, Planet
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_exoclock_priorities():
    """Fetches priority list from ExoClock."""
    url = "https://www.exoclock.space/database/planets_json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        priorities = {}
        # Data is a dict: {'55Cnce': {'name': '55Cnce', 'priority': 'medium', ...}, ...}
        if isinstance(data, dict):
             for key, val in data.items():
                 if isinstance(val, dict):
                     # Normalize key for robust matching (strip spaces, dashes, lower)
                     # ExoClock keys seem to be stripped already (55Cnce)
                     # NASA names have spaces (55 Cnc e)
                     # We will create a lookup map based on stripped names.
                     prio = val.get('priority', 'Normal')
                     
                     # Use the name from the value if present, otherwise key
                     raw_name = val.get('name', key)
                     
                     # Normalize: lowercase, remove spaces, remove dashes
                     norm_name = raw_name.lower().replace(" ", "").replace("-", "")
                     
                     # Store Title Case: "medium" -> "Medium"
                     priorities[norm_name] = prio.title()
                     
        return priorities
    except Exception as e:
        logger.error(f"Failed to fetch ExoClock data: {e}")
        return {}

def update_database(session_factory=None):
    """Fetches data from NASA and updates the local DB.
    
    Args:
        session_factory: Optional sessionmaker. Defaults to Postgres SessionLocal.
    """
    if session_factory:
        db = session_factory()
    else:
        db = SessionLocal()

    try:
        logger.info("Fetching data from NASA Exoplanet Archive...")
        # Query pscomppars for transiting planets
        # We need: pl_name, hostname, ra, dec, sy_vmag, pl_orbper, pl_tranmid, pl_trandur, pl_trandep
        # Filtering for pl_tranmid is not null to ensure we have ephemerides.
        nasa_table = NasaExoplanetArchive.query_criteria(
            table="pscomppars",
            select="pl_name,hostname,ra,dec,sy_vmag,pl_orbper,pl_tranmid,pl_trandur,pl_trandep",
            where="pl_tranmid is not null and pl_trandur is not null"
        )
        
        logger.info(f"Fetched {len(nasa_table)} planets from NASA.")
        
        exoclock_prio = fetch_exoclock_priorities()
        logger.info(f"Fetched {len(exoclock_prio)} priorities from ExoClock.")

        for row in nasa_table:
            pl_name = str(row['pl_name'])
            host_name = str(row['hostname'])
            
            # Helper to safely get float value
            def get_val(val, default=None):
                if hasattr(val, 'value'):
                    val = val.value
                if hasattr(val, 'fill_value'): # It is masked
                    val = val.filled(np.nan)
                
                # val should be a number or nan now
                try:
                    fval = float(val)
                    if np.isfinite(fval):
                        return fval
                except:
                    pass
                return default

            # Data conversion
            ra = get_val(row['ra'])
            dec = get_val(row['dec'])
            vmag = get_val(row['sy_vmag'])
            
            # Check if star exists
            star = db.query(Star).filter(Star.name == host_name).first()
            if not star:
                star = Star(
                    name=host_name,
                    ra=ra if ra is not None else 0.0,
                    dec=dec if dec is not None else 0.0,
                    mag_v=vmag
                )
                db.add(star)
                db.flush() # Get ID
            else:
                # Update existing star data
                if ra is not None: star.ra = ra
                if dec is not None: star.dec = dec
                star.mag_v = vmag

            
            # Check if planet exists
            planet = db.query(Planet).filter(Planet.name == pl_name).first()
            
            # Data conversion
            period = get_val(row['pl_orbper'], 0.0)
            t0 = get_val(row['pl_tranmid'], 0.0)
            duration = get_val(row['pl_trandur'], 0.0)
            depth_raw = get_val(row['pl_trandep'], 0.0)
            
            depth_mmag = 0.0
            if depth_raw > 0:
                depth_frac = depth_raw / 100.0
                if depth_frac < 1:
                    # np.log10 returns a numpy float, we must cast to python float
                    depth_mag = -2.5 * np.log10(1.0 - depth_frac)
                    depth_mmag = float(depth_mag * 1000.0)
            
            # Priority
            # Normalize NASA name
            norm_pl_name = pl_name.lower().replace(" ", "").replace("-", "")
            priority = exoclock_prio.get(norm_pl_name, "Normal") # Default to Normal

            if not planet:
                planet = Planet(
                    name=pl_name,
                    star_id=star.id,
                    period=period,
                    t0=t0,
                    duration=duration,
                    depth_mmag=depth_mmag,
                    priority=priority
                )
                db.add(planet)
            else:
                # Update logic
                planet.period = period
                planet.t0 = t0
                planet.duration = duration
                planet.depth_mmag = depth_mmag
                planet.priority = priority
        
        db.commit()
        logger.info("Database update complete.")
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        db.rollback()
    finally:
        db.close()
