import sys
import os

# Add the root directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORTANT: Load streamlit stub BEFORE importing anything else
# This prevents ImportError for modules that do `import streamlit as st`
import streamlit_stub  # noqa: F401 — registers stub into sys.modules on Vercel

from api_main import app

# Vercel needs a variable called 'app' or 'handler'
# Since api_main already has 'app', we just expose it.
