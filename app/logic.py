from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_body
import astropy.units as u
import numpy as np
import pandas as pd
from astroplan import Observer
from app.models import Planet, Star

def get_observer(lat, lon, elevation=0):
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=elevation*u.m)
    return Observer(location=location)

def calculate_transits_in_window(planet_data, start_time, end_time, observer, min_alt=30, max_sun_alt=-6):
    """
    Calculates transits for a single planet within a window.
    planet_data: dict or object with period, t0, duration, ra, dec
    """
    period = planet_data.period
    t0 = planet_data.t0
    duration_hours = planet_data.duration
    
    if not period or not t0:
        return []

    # Calculate N range
    # T_c = t0 + N * period
    # start <= t0 + N * period <= end
    # (start - t0)/period <= N <= (end - t0)/period
    
    t_start_jd = start_time.jd
    t_end_jd = end_time.jd
    
    n_start = np.ceil((t_start_jd - t0) / period)
    n_end = np.floor((t_end_jd - t0) / period)
    
    if n_start > n_end:
        return []
        
    transits = []
    target_coord = SkyCoord(ra=planet_data.ra*u.deg, dec=planet_data.dec*u.deg)
    
    for n in range(int(n_start), int(n_end) + 1):
        mid_jd = t0 + n * period
        # t0 is BJD_TDB, so mid_jd is in TDB scale.
        # We specify scale='tdb' so astropy handles conversion to UTC (for display/calc) correctly.
        mid_time = Time(mid_jd, format='jd', scale='tdb')
        
        # Check basic visibility at mid-transit
        # Sun constraint
        # Altitude constraint
        
        # Convert to AltAz
        altaz = observer.altaz(mid_time, target_coord)
        altitude = altaz.alt.deg
        
        # Sun Altitude
        sun_alt = observer.sun_altaz(mid_time).alt.deg
        
        if altitude >= min_alt and sun_alt <= max_sun_alt:
            # Detailed Info
            
            # Start/End of transit
            ingress_time = mid_time - (duration_hours / 24.0 / 2.0) * u.day
            egress_time = mid_time + (duration_hours / 24.0 / 2.0) * u.day
            
            # Meridian Flip?
            # If transit crosses meridian. Check LST vs RA?
            # Or simpler: check azimuth change or HA crossing 0.
            # Local Sidereal Time
            lst = observer.local_sidereal_time(mid_time)
            ha = (lst - target_coord.ra).wrap_at(180*u.deg)
            # if HA is near 0, it's near meridian. 
            # But "crosses meridian" means during the transit duration.
            
            lst_ingress = observer.local_sidereal_time(ingress_time)
            ha_ingress = (lst_ingress - target_coord.ra).wrap_at(180*u.deg).deg
            
            lst_egress = observer.local_sidereal_time(egress_time)
            ha_egress = (lst_egress - target_coord.ra).wrap_at(180*u.deg).deg
            
            meridian_flip = False
            # If signs differ (negative to positive or vice versa), it crossed 0.
            if np.sign(ha_ingress) != np.sign(ha_egress):
                 meridian_flip = True
                 
            # Moon
            moon_loc = get_body("moon", mid_time, location=observer.location)
            moon_sep = moon_loc.separation(target_coord).deg
            # Approximate illumination (0-1)
            # Can use astroplan.moon.moon_illumination(mid_time) if available or astropy
            # astroplan has it.
            try:
                from astroplan import moon_illumination
                moon_ill = moon_illumination(mid_time)
            except ImportError:
                 moon_ill = 0 # Fallback
            
            # Error Propagation
            # sigma_T = sqrt(sigma_t0^2 + (N * sigma_P)^2)
            t0_err = getattr(planet_data, 't0_err', 0.0) or 0.0
            period_err = getattr(planet_data, 'period_err', 0.0) or 0.0
            min_scope = getattr(planet_data, 'min_telescope_in', 0.0) or 0.0
            
            error_days = np.sqrt(t0_err**2 + (n * period_err)**2)
            error_min = error_days * 24 * 60
            
            transits.append({
                "planet_name": planet_data.name,
                "mid_time": mid_time,
                "ingress": ingress_time,
                "egress": egress_time,
                "altitude": altitude,
                "sun_alt": sun_alt,
                "meridian_flip": meridian_flip,
                "moon_sep": moon_sep,
                "moon_ill": moon_ill,
                "depth": planet_data.depth_mmag,
                "duration": duration_hours,
                "ra": planet_data.ra,
                "dec": planet_data.dec,
                "mag_v": planet_data.mag_v,
                "priority": planet_data.priority,
                "uncertainty_min": error_min,
                "min_telescope_in": min_scope
            })
            
    return transits

def calculate_sky_gradient(time_array, observer):
    """
    Returns a list of colors/conditions for the given time array.
    """
    # Vectorized sun altitude calculation is faster if possible, 
    # but astroplan sun_altaz might not be fully vectorized for large arrays efficiently without caching.
    # astropy get_sun is better.
    
    # Simple classification based on Sun Alt
    # > -6: Civil Twilight/Day (Blue/Light Grey)
    # -6 > x > -18: Nautical/Astro (Dark Blue)
    # < -18: Night (Black)
    
    sun_alt = observer.sun_altaz(time_array).alt.deg
    
    colors = []
    for alt in sun_alt:
        if alt > -6:
            colors.append("Civil") # Map to color in UI
        elif alt > -18:
            colors.append("Nautical")
        else:
            colors.append("Night")
    return colors, sun_alt

def calculate_moon_alt(time_array, observer):
    """Calculates Moon altitude for a given time array and observer."""
    moon_coords = get_body("moon", time_array, location=observer.location)
    moon_altaz = observer.altaz(time_array, moon_coords)
    return moon_altaz.alt.deg
