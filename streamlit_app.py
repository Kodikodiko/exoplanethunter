import streamlit as st
import sys
import os

# Add the current directory to sys.path to ensure 'app' package is found
sys.path.append(os.path.dirname(__file__))

# Import the main module from the app package
# This executes the Streamlit app logic defined in app/main.py
try:
    import app.main
    if hasattr(app.main, 'run'):
        app.main.run()
except ImportError as e:
    st.error(f"Failed to import application: {e}")
