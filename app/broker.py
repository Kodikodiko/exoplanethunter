import requests
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
from app.database import SessionLocal
from app.models import Star, Planet
import numpy as np
import logging
from astropy.coordinates import SkyCoord
import astropy.units as u

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_exoclock_data():
    """Fetches full planet data from ExoClock."""
    url = "https://www.exoclock.space/database/planets_json"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.error(f"Failed to fetch ExoClock data: {e}")
        return {}

def normalize_name(name):
    """Normalizes planet name for comparison (lowercase, no spaces/dashes)."""
    if not name: return ""
    return str(name).lower().replace(" ", "").replace("-", "")

def update_database(session_factory=None):
    """Fetches data from ExoClock (primary) and NASA (fallback) to update local DB.
    
    Args:
        session_factory: Optional sessionmaker. Defaults to Postgres SessionLocal.
    """
    if session_factory:
        db = session_factory()
    else:
        db = SessionLocal()

    processed_planets = set()

    try:
        # 1. Fetch ExoClock Data (Primary Source)
        logger.info("Fetching data from ExoClock...")
        exoclock_data = fetch_exoclock_data()
        logger.info(f"Fetched {len(exoclock_data)} planets from ExoClock.")
        
        for key, val in exoclock_data.items():
            try:
                # Key is usually normalized (e.g. 55Cnce), val['name'] might be nicer
                raw_name = val.get('name', key)
                norm_name = normalize_name(raw_name)
                
                # Coordinates (ExoClock uses Sexagesimal strings often: "08:52:35...", "+28:19:...")
                ra_str = val.get('ra_j2000')
                dec_str = val.get('dec_j2000')
                
                ra = 0.0
                dec = 0.0
                if ra_str and dec_str:
                    try:
                        coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                        ra = float(coord.ra.deg)
                        dec = float(coord.dec.deg)
                    except Exception as coord_err:
                        logger.warning(f"Could not parse coords for {raw_name}: {coord_err}")

                vmag_val = val.get('v_mag')
                if vmag_val is None:
                    # Fallback to other mags if V is missing
                    vmag_val = val.get('gaia_g_mag') or val.get('r_mag') or 0.0
                
                # Ensure vmag is a python float
                try:
                    vmag = float(vmag_val)
                except:
                    vmag = 0.0
                
                host_name = val.get('star', raw_name) # Sometimes star name isn't explicit?
                
                # --- Star Upsert ---
                # Try to find star by name (normalized?) or just raw name match?
                # Stars are harder to normalize perfectly without a catalog. 
                # We'll stick to the provided star name.
                star = db.query(Star).filter(Star.name == host_name).first()
                if not star:
                    star = Star(name=host_name, ra=ra, dec=dec, mag_v=vmag)
                    db.add(star)
                    db.flush()
                else:
                    star.ra = ra
                    star.dec = dec
                    star.mag_v = vmag
                
                # --- Planet Upsert ---
                # ExoClock fields: 
                # ephem_mid_time (BJD_TDB), ephem_period (Days)
                # duration_hours
                # depth_r_mmag (Use this for depth)
                
                def to_float(x):
                    try:
                        return float(x)
                    except:
                        return 0.0

                t0 = to_float(val.get('ephem_mid_time') or val.get('t0_bjd_tdb'))
                period = to_float(val.get('ephem_period') or val.get('period_days'))
                duration = to_float(val.get('duration_hours'))
                depth = to_float(val.get('depth_r_mmag')) # This is usually mmag directly?
                
                # Uncertainty & Equipment
                # Take absolute value of error if provided
                period_err = abs(to_float(val.get('period_unc') or val.get('ephem_period_e1')))
                t0_err = abs(to_float(val.get('t0_unc') or val.get('ephem_mid_time_e1')))
                min_scope = to_float(val.get('min_telescope_inches'))

                # Inspecting JSON from before: "depth_r_mmag": 0.45.
                # User's CSV shows "depth": 8.22. 
                # Wait, 0.45 mmag is tiny. Maybe it's percent? 
                # Let's check ExoClock definitions. "depth_r_mmag" implies mmag.
                # 55 Cnc e is shallow. 
                # User CSV: WASP-118 b depth 8.22. (Usually ~1%). 1% ~ 10 mmag.
                # So depth_r_mmag is likely millimagnitudes.
                
                prio = val.get('priority', 'Normal').title()
                
                planet = db.query(Planet).filter(Planet.name == raw_name).first()
                if not planet:
                    planet = Planet(
                        name=raw_name,
                        star_id=star.id,
                        period=period,
                        t0=t0,
                        duration=duration,
                        depth_mmag=depth,
                        period_err=period_err,
                        t0_err=t0_err,
                        min_telescope_in=min_scope,
                        priority=prio
                    )
                    db.add(planet)
                else:
                    planet.period = period
                    planet.t0 = t0
                    planet.duration = duration
                    planet.depth_mmag = depth
                    planet.period_err = period_err
                    planet.t0_err = t0_err
                    planet.min_telescope_in = min_scope
                    planet.priority = prio
                
                processed_planets.add(norm_name)
                
            except Exception as item_err:
                logger.error(f"Error processing ExoClock item {key}: {item_err}")
                continue

        db.commit() # Commit ExoClock batch
        
        # 2. Fetch NASA Data (Fallback)
        logger.info("Fetching data from NASA Exoplanet Archive...")
        nasa_table = NasaExoplanetArchive.query_criteria(
            table="pscomppars",
            select="pl_name,hostname,ra,dec,sy_vmag,pl_orbper,pl_tranmid,pl_trandur,pl_trandep",
            where="pl_tranmid is not null and pl_trandur is not null"
        )
        logger.info(f"Fetched {len(nasa_table)} planets from NASA.")
        
        for row in nasa_table:
            pl_name = str(row['pl_name'])
            norm_name = normalize_name(pl_name)
            
            if norm_name in processed_planets:
                continue # Skip, we have better data
                
            host_name = str(row['hostname'])
            
            def get_val(val, default=None):
                if hasattr(val, 'value'): val = val.value
                if hasattr(val, 'fill_value'): val = val.filled(np.nan)
                try:
                    fval = float(val)
                    if np.isfinite(fval): return fval
                except: pass
                return default

            ra = get_val(row['ra'])
            dec = get_val(row['dec'])
            vmag = get_val(row['sy_vmag'])
            
            star = db.query(Star).filter(Star.name == host_name).first()
            if not star:
                star = Star(
                    name=host_name,
                    ra=ra if ra is not None else 0.0,
                    dec=dec if dec is not None else 0.0,
                    mag_v=vmag
                )
                db.add(star)
                db.flush()
            else:
                # Only update if we are the primary source for this star (optional)
                # But a star might host multiple planets, some in ExoClock, some not.
                # We'll just update if values exist.
                if ra is not None: star.ra = ra
                if dec is not None: star.dec = dec
                if vmag is not None: star.mag_v = vmag

            planet = db.query(Planet).filter(Planet.name == pl_name).first()
            
            period = get_val(row['pl_orbper'], 0.0)
            t0 = get_val(row['pl_tranmid'], 0.0)
            duration = get_val(row['pl_trandur'], 0.0)
            depth_raw = get_val(row['pl_trandep'], 0.0) # Usually percent
            
            depth_mmag = 0.0
            if depth_raw > 0:
                # Convert percent to mmag
                # delta_mag = -2.5 * log10(1 - depth_frac)
                depth_frac = depth_raw / 100.0
                if depth_frac < 1:
                    depth_mag = -2.5 * np.log10(1.0 - depth_frac)
                    depth_mmag = float(depth_mag * 1000.0)
            
            # Priority default
            priority = "Normal"

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
                planet.period = period
                planet.t0 = t0
                planet.duration = duration
                planet.depth_mmag = depth_mmag
                # Don't overwrite priority if it was set manually, but here we treat NASA as fresh insert for non-ExoClock
                planet.priority = priority
        
        db.commit()
        logger.info("Database update complete.")
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        db.rollback()
    finally:
        db.close()
