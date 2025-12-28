import streamlit as st

def apply_theme(theme_mode):
    """
    Injects CSS based on the selected theme.
    """
    css = ""
    
    # We use Streamlit's semantic CSS variables to override the theme dynamically.
    # Base theme is Dark (from config.toml).
    
    if theme_mode == "Dark":
        # Default behavior (matches config.toml), but we enforce it to be sure
        css = """
        <style>
        :root {
            --primary-color: #38bdf8;
            --background-color: #0f172a;
            --secondary-background-color: #1e293b;
            --text-color: #e2e8f0;
            --font: sans-serif;
        }
        /* Ensure inputs match */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stSelectbox, .stMultiSelect {
            color: #e2e8f0 !important;
            background-color: #1e293b !important;
        }
        </style>
        """
        
    elif theme_mode == "Light":
        # Override variables for Light Mode
        css = """
        <style>
        :root, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            --primary-color: #0284c7;
            --background-color: #ffffff;
            --secondary-background-color: #f1f5f9;
            --text-color: #0f172a;
        }
        
        /* Force background and text application */
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        [data-testid="stSidebar"] {
            background-color: var(--secondary-background-color);
        }
        
        /* Fix Input Widgets which might default to Dark styles */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {
            color: #0f172a !important;
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
        }
        /* Selectbox/Multiselect text */
        .stSelectbox div[data-baseweb="select"] > div {
             background-color: #ffffff !important;
             color: #0f172a !important;
        }
        span[data-baseweb="tag"] {
            background-color: #e2e8f0 !important;
            color: #0f172a !important;
        }
        
        /* Dataframe fixes */
        [data-testid="stDataFrame"] {
            color: #0f172a !important;
        }
        </style>
        """
        
    elif theme_mode == "Nightsight (Red)":
        # Red Mode: Force Black BG, Red Text, and Filter
        css = """
        <style>
        :root, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
            --primary-color: #ff0000;
            --background-color: #000000;
            --secondary-background-color: #000000;
            --text-color: #ff0000;
        }
        
        [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {
            background-color: #000000 !important;
            color: #ff0000 !important;
        }
        
        /* Apply Filter to turn everything red/monochrome */
        /* We filter the main container to catch charts and maps */
        [data-testid="stAppViewContainer"] {
            filter: grayscale(100%) sepia(100%) hue-rotate(-50deg) saturate(600%) brightness(0.8);
        }
        [data-testid="stSidebar"] {
            filter: grayscale(100%) sepia(100%) hue-rotate(-50deg) saturate(600%) brightness(0.8);
            border-right: 1px solid #330000;
        }
        
        /* Text Colors */
        * {
            color: #ff0000 !important;
        }
        
        /* Chart lines override */
        .js-plotly-plot .scatterlayer .trace .lines path {
            stroke: #ff0000 !important;
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
