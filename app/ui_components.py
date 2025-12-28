import streamlit as st

def apply_theme(theme_mode):
    """
    Injects CSS based on the selected theme.
    Base theme is set to DARK in .streamlit/config.toml.
    """
    css = ""
    
    if theme_mode == "Dark":
        # Native Streamlit Dark (from config.toml)
        # We don't need extra CSS here to avoid "black screen" bugs
        pass

    elif theme_mode == "Light":
        # Force Light Theme
        css = """
        <style>
        .stApp {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f1f5f9 !important;
        }
        /* Text overrides */
        p, h1, h2, h3, h4, h5, h6, label, span {
            color: #0f172a !important;
        }
        /* Input fields */
        input {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
        }
        </style>
        """

    elif theme_mode == "Nightsight (Red)":
        # Nightsight Mode
        css = """
        <style>
        .stApp, [data-testid="stSidebar"] {
            background-color: #000000 !important;
            color: #ff0000 !important;
        }
        .stApp {
             filter: grayscale(100%) sepia(100%) hue-rotate(-50deg) saturate(600%) brightness(0.8);
        }
        * {
            color: #ff0000 !important;
        }
        </style>
        """
    
    if css:
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
