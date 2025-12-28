import streamlit as st

def apply_theme(theme_mode):
    """
    Injects CSS based on the selected theme.
    Assumes Streamlit default theme is LIGHT.
    """
    css = ""
    
    if theme_mode == "Light":
        # Native Streamlit Light Theme - No overrides needed
        pass

    elif theme_mode == "Dark":
        # Force Dark Theme over the native Light Theme
        css = """
        <style>
        :root {
            --primary-color: #38bdf8;
            --background-color: #0f172a;
            --secondary-background-color: #1e293b;
            --text-color: #e2e8f0;
        }
        
        /* Main Backgrounds */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        [data-testid="stSidebar"] {
            background-color: var(--secondary-background-color);
        }
        
        /* Text Color Overrides for all elements */
        h1, h2, h3, h4, h5, h6, p, div, span, label, li {
            color: var(--text-color) !important;
        }
        
        /* Inputs: Dark Background, Light Text */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stSelectbox, .stMultiSelect {
            background-color: #334155 !important;
            color: #f1f5f9 !important;
            border-color: #475569 !important;
        }
        
        /* Dropdowns/Popups (Selectbox options) - Hard to target, but try */
        div[data-baseweb="popover"] div {
            background-color: #1e293b !important;
            color: #e2e8f0 !important;
        }
        
        /* Dataframes */
        [data-testid="stDataFrame"] {
            background-color: var(--background-color) !important;
        }
        [data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span {
            color: var(--text-color) !important;
        }
        </style>
        """
        
    elif theme_mode == "Nightsight (Red)":
        # Red Mode: Force Black BG, Red Text, and Filter
        css = """
        <style>
        /* Force defaults to black/red before filter */
        .stApp, [data-testid="stSidebar"] {
            background-color: black !important;
            color: #ff3333 !important;
        }
        
        /* Filter everything to red */
        html {
            filter: grayscale(100%) brightness(0.7) sepia(100%) hue-rotate(-50deg) saturate(500%) contrast(1.2);
        }
        
        /* Force text to be bright so it passes through filter visible */
        * {
            color: #ffcccc !important; 
        }
        
        /* Graphs lines */
        .js-plotly-plot .scatterlayer .trace .lines path {
            stroke: #ff3333 !important;
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
