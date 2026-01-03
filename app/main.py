import sys
import os

# Add project root to path to ensure absolute imports work on Streamlit Cloud
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import app.warnings_config # Import this first to silence warnings
from datetime import datetime, timedelta, time
from app.ui_components import apply_theme, render_sidebar
from app.database import SessionLocal, engine, Base, get_session_factory
from app.models import Planet, Star
from app.broker import update_database
from app.logic import get_observer, calculate_transits_in_window, calculate_sky_gradient, calculate_moon_alt
import plotly.graph_objects as go
import requests
import json
import numpy as np
import astropy.units as u

# Init DB Tables if not exist
# Note: For SQLite, this might need to run on the specific engine if we switch dynamically,
# but our export script already creates tables.
# Base.metadata.create_all(bind=engine) 

def run():
    st.set_page_config(page_title="ExoHunter Pro", layout="wide", page_icon="🔭")

    # Sidebar & Config
    config = render_sidebar()
    apply_theme(config['theme'])

    st.sidebar.divider()
    # Data Source Toggle
    data_source = st.sidebar.radio("Data Source", ["PostgreSQL", "SQLite"])
    Session = get_session_factory(data_source)

    st.sidebar.divider()
    nina_ip = st.sidebar.text_input("N.I.N.A IP Address", value="192.168.1.50")
    nina_port = st.sidebar.text_input("N.I.N.A Port", value="1888")

    # Main Layout
    st.title("ExoHunter Pro 🔭")
    st.caption("Advanced Exoplanet Transit Planner")

    # Database Status / Update
    if st.sidebar.button("Update Database (NASA/ExoClock)"):
        if data_source == "SQLite":
            st.sidebar.warning("Updating the static SQLite file will only persist for this session on cloud deployments.")
        
        with st.spinner("Fetching data from NASA Exoplanet Archive & ExoClock... This may take a minute."):
            update_database(Session)
        st.sidebar.success("Database updated successfully!")

    # Search Filters
    with st.expander("Search Parameters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search_date = st.date_input("Observation Date", value=datetime.now())
            start_hour = st.time_input("Start Time", value=time(18, 0))
        with col2:
            end_date_offset = st.number_input("Window Duration (Hours)", value=168, min_value=1, max_value=336)
            min_alt = st.number_input("Min Altitude (°)", value=30)
        with col3:
            min_depth = st.number_input("Min Depth (mmag)", value=5.0)
            max_mag = st.number_input("Max Magnitude (V)", value=14.0)
        with col4:
            # Priority Filter
            priorities = st.multiselect("Priority (ExoClock)", ["High", "Medium", "Low", "Normal", "Alert"], default=["High", "Alert"])

    # Logic
    if st.button("Find Transits"):
        db = Session()
        
        # 1. Static Filter (SQL)
        query = db.query(Planet, Star).join(Star).filter(
            Star.mag_v <= max_mag,
            Planet.depth_mmag >= min_depth
        )
        
        if priorities:
            query = query.filter(Planet.priority.in_(priorities))
            
        candidates = query.all()
        db.close()
        
        st.write(f"Analyzing {len(candidates)} candidates matching static criteria...")
        
        # 2. Dynamic Calculation
        start_dt = datetime.combine(search_date, start_hour)
        end_dt = start_dt + timedelta(hours=end_date_offset)
        
        from astropy.time import Time
        t_start = Time(start_dt)
        t_end = Time(end_dt)
        
        observer = get_observer(config['lat'], config['lon'], config['elevation'])
        
        progress_bar = st.progress(0)
        
        valid_transits = []
        
        for i, (planet, star) in enumerate(candidates):
            if i % max(1, len(candidates)//10) == 0:
                progress_bar.progress(i / len(candidates))
                
            planet_data = planet
            planet_data.ra = star.ra
            planet_data.dec = star.dec
            planet_data.mag_v = star.mag_v
            
            transits = calculate_transits_in_window(planet_data, t_start, t_end, observer, min_alt=min_alt)
            valid_transits.extend(transits)
            
        progress_bar.progress(100)
        
        # Sort by mid_time ascending (soonest first)
        valid_transits.sort(key=lambda x: x['mid_time'])
        
        # Filter by Aperture
        initial_count = len(valid_transits)
        valid_transits = [t for t in valid_transits if t.get('min_telescope_in', 0) <= config['aperture']]
        hidden_count = initial_count - len(valid_transits)
        
        # Store results in session state
        st.session_state['transits_data'] = valid_transits
        st.session_state['search_performed'] = True
        st.session_state['hidden_count'] = hidden_count

    if st.session_state.get('search_performed', False):
        valid_transits = st.session_state.get('transits_data', [])
        hidden_count = st.session_state.get('hidden_count', 0)

        if not valid_transits:
            if hidden_count > 0:
                st.warning(f"No transits found for your aperture ({hidden_count} hidden). Try increasing aperture in sidebar.")
            else:
                st.warning("No transits found matching criteria.")
        else:
            if hidden_count > 0:
                st.caption(f"ℹ️ Hidden {hidden_count} candidates requiring aperture > {config['aperture']}\"")
                
            st.success(f"Found {len(valid_transits)} observable transits.")
            # Display Results
            df = pd.DataFrame(valid_transits)
            
            # Re-create observer for detail view calculations (needed on rerun)
            observer = get_observer(config['lat'], config['lon'], config['elevation'])
            
            # Create display copy with proper formatting
            df_display = df.copy()
            if not df_display.empty:
                # Format Uncertainty
                df_display['uncertainty'] = df_display['uncertainty_min'].apply(
                    lambda x: f"± {x:.0f} min" if x > 0 else "--"
                )
                
                # Format: dd.mm.yyyy HH:MM
                # Add warning icon if uncertainty is high
                def format_time_with_warning(row):
                    t_str = row['mid_time'].to_datetime().strftime('%d.%m.%Y %H:%M') if hasattr(row['mid_time'], 'to_datetime') else str(row['mid_time'])
                    if row.get('uncertainty_min', 0) > 30:
                        return f"⚠️ {t_str}"
                    return t_str
                
                df_display['mid_time'] = df_display.apply(format_time_with_warning, axis=1)

            # --- Layout Change: Table + Detail View ---
            
            # Define Columns to display
            display_cols = ["planet_name", "mid_time", "uncertainty", "altitude", "depth", "duration", "mag_v", "priority", "moon_ill"]
            
            col_list, col_detail = st.columns([1.5, 2.5]) # Left: Table, Right: Graph
            
            with col_list:
                st.markdown("### Candidates")
                # Configure dataframe with selection
                # Note: on_select is available in recent Streamlit. 
                # If selection_mode="single-row" is used, st.dataframe returns a selection object.
                
                event = st.dataframe(
                    df_display[display_cols].style.format({
                        "altitude": "{:.1f}",
                        "depth": "{:.2f}",
                        "duration": "{:.2f}",
                        "mag_v": "{:.1f}",
                        "moon_ill": "{:.2f}"
                    }),
                    width="stretch", # Make it fit the column
                    hide_index=True,
                    selection_mode="single-row",
                    on_select="rerun",
                    key="transit_table"
                )
                
                # CSV Download for ALL results
                if not df_display.empty:
                     csv_data = df_display.to_csv(index=False)
                     st.download_button(
                         label="Download Results CSV",
                         data=csv_data,
                         file_name=f"exohunter_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                         mime="text/csv",
                         key="download_all_csv"
                     )
            
            selected_rows = event.selection.rows
            
            with col_detail:
                if selected_rows:
                    idx = selected_rows[0]
                    row = df.iloc[idx] # Use original DF with Time objects
                    
                    # Header matches Left Column
                    st.markdown(f"### {row['planet_name']}")
                    
                    formatted_time = row['mid_time'].to_datetime().strftime('%d.%m.%Y %H:%M')
                    unc_min = row.get('uncertainty_min', 0)
                    unc_str = f"(± {unc_min:.0f} min)" if unc_min > 0 else ""
                    
                    # --- Plotly Logic (Reused) ---
                    dur_days = row['duration'] / 24.0
                    plot_start = row['mid_time'] - (dur_days * 1.5) * u.day
                    plot_end = row['mid_time'] + (dur_days * 1.5) * u.day
                    
                    times = plot_start + (plot_end - plot_start) * np.linspace(0, 1, 100)
                    
                    min_flux = 10**(-row['depth']/1000.0 / 2.5)
                    ingress_dur = (row['duration'] / 10.0) / 24.0 
                    half_dur = (row['duration'] / 2.0) / 24.0
                    
                    flux = []
                    mid_jd = row['mid_time'].jd
                    
                    for t in times.jd:
                        dt = abs(t - mid_jd)
                        if dt <= (half_dur - ingress_dur):
                            flux.append(min_flux)
                        elif dt <= half_dur:
                            frac = (half_dur - dt) / ingress_dur
                            flux.append(1.0 - (1.0 - min_flux) * frac)
                        else:
                            flux.append(1.0)
                    
                    colors, _ = calculate_sky_gradient(times, observer)
                    moon_alts = calculate_moon_alt(times, observer)
                    
                    fig = go.Figure()
                    
                    color_map = {
                        "Civil": "rgba(135, 206, 235, 0.3)", 
                        "Nautical": "rgba(0, 0, 139, 0.5)", 
                        "Night": "rgba(0, 0, 0, 0.8)" 
                    }
                    if config['theme'] == "Nightsight (Red)":
                         color_map = {
                            "Civil": "rgba(50, 0, 0, 0.3)",
                            "Nautical": "rgba(100, 0, 0, 0.5)",
                            "Night": "rgba(0, 0, 0, 0.9)"
                        }
                    
                    shapes = []
                    if len(times) > 1:
                        current_color = colors[0]
                        start_idx = 0
                        for i in range(1, len(colors)):
                            if colors[i] != current_color:
                                rect_start = times[start_idx].isot
                                rect_end = times[i].isot
                                shapes.append(dict(
                                    type="rect", xref="x", yref="paper", x0=rect_start, y0=0, x1=rect_end, y1=1,
                                    fillcolor=color_map.get(current_color, "black"), opacity=0.5, layer="below", line_width=0,
                                ))
                                current_color = colors[i]
                                start_idx = i
                        shapes.append(dict(
                            type="rect", xref="x", yref="paper", x0=times[start_idx].isot, y0=0, x1=times[-1].isot, y1=1,
                            fillcolor=color_map.get(current_color, "black"), opacity=0.5, layer="below", line_width=0,
                        ))

                    fig.add_trace(go.Scatter(
                        x=times.isot, y=flux, mode='lines', name='Flux',
                        line=dict(color='red' if config['theme'] == "Nightsight (Red)" else 'orange', width=3)
                    ))
                    
                    # Add Moon Altitude (Secondary Y)
                    fig.add_trace(go.Scatter(
                        x=times.isot, y=moon_alts, name='Moon Alt', yaxis='y2', line=dict(color='white', dash='dot')
                    ))
                    
                    # Title with Info
                    plot_title = f"Transit Lightcurve {unc_str}<br><sup style='color: gray'>Time: {formatted_time} | Mag: {row['mag_v']:.1f} | Depth: {row['depth']:.1f} mmag</sup>"
                    if config['theme'] == "Nightsight (Red)":
                         plot_title = f"Transit Lightcurve {unc_str}<br><sup style='color: red'>Time: {formatted_time} | Mag: {row['mag_v']:.1f} | Depth: {row['depth']:.1f} mmag</sup>"

                    fig.update_layout(
                        title=dict(text=plot_title),
                        xaxis_title="Time (UTC)",
                        yaxis_title="Relative Flux",
                        yaxis2=dict(title="Moon Altitude", overlaying="y", side="right", range=[-90, 90]),
                        shapes=shapes,
                        template="plotly_dark" if config['theme'] != "Light" else "plotly_white",
                        margin=dict(l=20, r=20, t=50, b=20), # Increase top margin for title
                        height=450
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Actions
                    if st.button(f"Send {row['planet_name']} to N.I.N.A"):
                         # ... NINA logic ...
                         try:
                            payload = {"Name": row['planet_name'], "Coordinates": {"RA": row['ra'], "Dec": row['dec']}}
                            url = f"http://{nina_ip}:{nina_port}/api/v1/targets/add"
                            st.info(f"Mock: Sent {row['planet_name']} to {url}")
                         except Exception as e:
                            st.error(f"Failed: {e}")
                else:
                    st.info("Select a transit from the table on the left to see details.")

if __name__ == "__main__":
    run()
