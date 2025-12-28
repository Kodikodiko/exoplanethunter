import streamlit as st

def apply_theme(theme_mode):
    """
    Injects CSS based on the selected theme.
    """
    css = ""
    # Define variables based on mode
    if theme_mode == "Dark":
        # Matches config.toml defaults, but re-enforcing here ensures consistency if config fails
        css = """
        <style>
        :root {
            --primary-color: #38bdf8;
            --background-color: #0f172a;
            --secondary-background-color: #1e293b;
            --text-color: #e2e8f0;
        }
        </style>
        """
    elif theme_mode == "Light":
        css = """
        <style>
        :root {
            --primary-color: #0284c7;
            --background-color: #ffffff;
            --secondary-background-color: #f1f5f9;
            --text-color: #0f172a;
        }
        </style>
        """
    elif theme_mode == "Nightsight (Red)":
        # Global Red Filter
        # We handle this via filter on the html/body
        pass

    # Apply Variables to Elements
    # We apply these rules for Dark and Light. Red is special.
    if theme_mode != "Nightsight (Red)":
        css += """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        [data-testid="stSidebar"] {
            background-color: var(--secondary-background-color);
        }
        [data-testid="stHeader"] {
            background-color: transparent;
        }
        /* Force text colors for Light mode overrides */
        div, p, h1, h2, h3, h4, span, label {
            color: var(--text-color) !important;
        }
        /* Sidebar text */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: var(--text-color) !important;
        }
        </style>
        """
    
    # Red Mode Logic (Filter based)
    if theme_mode == "Nightsight (Red)":
        css = """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #ff0000 !important;
        }
        /* Filter everything to red */
        [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {
             filter: grayscale(100%) sepia(100%) hue-rotate(-50deg) saturate(600%) contrast(1.2) brightness(0.8);
        }
        </style>
        """
    
    st.markdown(css, unsafe_allow_html=True)

def render_sidebar():
    st.sidebar.header("Configuration")
    
    # Location
    st.sidebar.subheader("Observer Location")
    lat = st.sidebar.number_input("Latitude", value=48.0880, step=0.1, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=15.7566, step=0.1, format="%.4f")
    elevation = st.sidebar.number_input("Elevation (m)", value=640, step=10)
    
    st.sidebar.divider()
    
    # Theme
    st.sidebar.subheader("Theme")
    theme = st.sidebar.radio("Mode", ["Dark", "Light", "Nightsight (Red)"])
    
    return {
        "lat": lat,
        "lon": lon,
        "elevation": elevation,
        "theme": theme
    }
