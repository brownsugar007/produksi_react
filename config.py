"""
Centralized Configuration & Constants

Loads environment variables and validates required settings at startup.
"""
import os
import sys
import time
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# ── Environment Variable Validation ───────────────────────────
def validate_environment():
    """
    Validate that all required environment variables are set.
    Raises EnvironmentError if any required variable is missing.
    """
    required_vars = {
        "AZURE_TENANT_ID": "Azure AD Tenant ID",
        "AZURE_CLIENT_ID": "Azure AD Client ID (Application ID)",
        "AZURE_CLIENT_SECRET": "Azure AD Client Secret"
    }

    missing_vars = []

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        
        # Check Streamlit Secrets if available
        if not value:
            try:
                import streamlit as st
                if var_name in st.secrets:
                    value = st.secrets[var_name]
                    os.environ[var_name] = value
            except:
                pass
                
        if not value or value.strip() == "":
            missing_vars.append(f"• {var_name}: {description}")

    if missing_vars:
        error_msg = "Missing Required Environment Variables:\n" + "\n".join(missing_vars)
        print(error_msg)
        # Only use st.error if streamlit is actually running
        try:
            import streamlit as st
            if st._is_running_with_streamlit:
                st.error(error_msg)
                st.stop()
        except:
            pass
        raise EnvironmentError(error_msg)

    return True

# Validate environment on import
validate_environment()

# ── OneDrive Links ────────────────────────────────────────────
ONEDRIVE_LINKS = {
    "db_hourly": "https://mgeid-my.sharepoint.com/:x:/r/personal/planning_department_mgeid_onmicrosoft_com/Documents/Dashboard_all/db%20Production%20Hourly%20(final).xlsx?d=w24cf5b9c64854d42915913d3e7671764&csf=1&web=1&e=bKZhbL",
    "plan_hourly": "https://mgeid-my.sharepoint.com/:x:/g/personal/planning_department_mgeid_onmicrosoft_com/IQBK3837O3nsR5AKLRsno8PGARKNx5EqiQV3IbnLXQayihk?e=BxFbTc",
}

# ── Cache Settings ────────────────────────────────────────────
CACHE_TTL_SECONDS = 60
SYNC_INTERVAL = 60
# Vercel has a read-only filesystem except for /tmp
if os.getenv("VERCEL"):
    CACHE_FILE = "/tmp/cache.pkl"
else:
    CACHE_FILE = "data/cache.pkl"
    # Ensure data directory exists locally
    Path("data").mkdir(parents=True, exist_ok=True)

# ── Azure AD / Microsoft Graph API ─────────────────────────────
# All Azure credentials must be set in .env file or Streamlit Secrets (validated above)
AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")

# Optional: Specific file IDs for the Excel workbooks (if using Graph API with file IDs)
FILE_IDS = {
    "db_hourly": os.getenv("FILE_IDS_DB_HOURLY", ""),
    "plan_hourly": os.getenv("FILE_IDS_PLAN_HOURLY", ""),
}

# ── Retry Settings ────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, exponential

# ── Achievement Thresholds ────────────────────────────────────
ACH_THRESHOLD_GOOD = 100  # >= this = green (target met)
ACH_THRESHOLD_WARN = 80   # >= this = orange (warning)

# ── Operational Hour Order ────────────────────────────────────
OP_HOURS = [f"{h:02d}" for h in range(6, 24)] + ["O0", "O1", "O2", "O3", "O4", "O5"]

# ── PIT Registry ─────────────────────────────────────────────
PIT_REGISTRY = {
    "North JO IC": {
        "icon": "🔵",
        "group": "North JO",
        "has_ct_plan": True,
        "label": "North JO IC",
    },
    "North JO GAM": {
        "icon": "🟢",
        "group": "North JO",
        "has_ct_plan": False,
        "label": "North JO GAM",
    },
    "South JO IC": {
        "icon": "🟠",
        "group": "South JO",
        "has_ct_plan": False,
        "label": "South JO IC",
    },
    "South JO GAM": {
        "icon": "🟣",
        "group": "South JO",
        "has_ct_plan": False,
        "label": "South JO GAM",
    },
}

# ── Color Palette ────────────────────────────────────────────
COLORS = {
    # Primary brand colors
    "primary": "#6366f1",      # Indigo 500
    "primary_light": "#818cf8",  # Indigo 400
    "primary_dark": "#4f46e5",   # Indigo 600

    # Semantic colors
    "success": "#10b981",      # Emerald 500
    "success_light": "#34d399", # Emerald 400
    "success_dark": "#059669",   # Emerald 600

    "danger": "#ef4444",       # Red 500
    "danger_light": "#f87171",  # Red 400
    "danger_dark": "#dc2626",    # Red 600

    "warning": "#f59e0b",      # Amber 500
    "warning_light": "#fbbf24", # Amber 400
    "warning_dark": "#d97706",   # Amber 600

    # Teal/Cyan variants (for charts)
    "teal": "#14b8a6",         # Teal 500
    "teal_light": "#5eead4",    # Teal 300
    "teal_dark": "#0f766e",      # Teal 700
    "teal_bg": "rgba(20, 184, 166, 0.1)",

    # Neutral grays
    "gray_50": "#f9fafb",
    "gray_100": "#f3f4f6",
    "gray_200": "#e5e7eb",
    "gray_300": "#d1d5db",
    "gray_400": "#9ca3af",
    "gray_500": "#6b7280",
    "gray_600": "#4b5563",
    "gray_700": "#374151",
    "gray_800": "#1f2937",
    "gray_900": "#111827",

    # Background colors
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8fafc",
    "bg_tertiary": "#f1f5f9",
}

# ── Production Units ─────────────────────────────────────────
UNITS = {
    "ob": "BCM",
    "coal_hauling": "MT",
    "coal_transit": "MT",
    "stock": "MT",
}
