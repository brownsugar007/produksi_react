"""
Azure API — Microsoft Graph Integration for Excel Data
Uses Client Credentials flow (Application Permissions) for background syncing.
"""
import requests
import msal
import io
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from config import AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, CACHE_TTL_SECONDS

AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

def get_access_token() -> Optional[str]:
    """Get Azure AD access token using Client Credentials flow."""
    app = msal.ConfidentialClientApplication(
        AZURE_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=AZURE_CLIENT_SECRET,
    )
    
    # Try getting token from cache first
    result = app.acquire_token_silent(SCOPES, account=None)
    
    if not result:
        # Fetch new token
        result = app.acquire_token_for_client(scopes=SCOPES)
        
    if "access_token" in result:
        return result["access_token"]
    
    logger.error(f"Azure Auth Error: {result.get('error_description', result.get('error'))}")
    return None

def download_excel_from_graph(url_or_id: str) -> Optional[dict[str, pd.DataFrame]]:
    """
    Download Excel workbook from Graph API and return all sheets.
    url_or_id can be a direct Graph content URL or a File ID.
    """
    import logging
    logger = logging.getLogger(__name__)

    token = get_access_token()
    if not token:
        logger.error("Failed to get Azure access token")
        return None

    headers = {"Authorization": f"Bearer {token}"}

    # If it's a file ID, construct the Graph URL for content
    # For company-shared files, we usually use /sites/{site-id}/drive/items/{item-id}/content
    # or /users/{user-id}/drive/items/{item-id}/content
    # Since we have the share link, we can use the 'shares' API to get the content directly

    # Helper to convert share link to graph download URL
    import base64
    try:
        # Need to encode the full sharing URL
        encoded_url = base64.urlsafe_b64encode(url_or_id.encode()).decode().rstrip("=")
        api_url = f"https://graph.microsoft.com/v1.0/shares/u!{encoded_url}/driveItem/content"
        logger.info(f"Trying Azure Graph API URL: {api_url}")
    except Exception as e:
        logger.error(f"Failed to encode URL: {e}")
        return None

    try:
        logger.info(f"Attempting Azure Graph API download...")
        response = requests.get(api_url, headers=headers, timeout=60)

        # Log response details
        logger.info(f"Azure Graph API response status: {response.status_code}")
        logger.info(f"Azure Graph API content-type: {response.headers.get('content-type', 'unknown')}")

        if response.status_code != 200:
            logger.error(f"Azure Graph API returned status {response.status_code}")
            logger.error(f"Response body: {response.text[:500]}")
            response.raise_for_status()

        # Validate we got a valid Excel file
        if len(response.content) < 4:
            logger.error("Downloaded content is too small to be a valid Excel file")
            return None

        # Check for ZIP signature (PK) which Excel files (.xlsx) use
        if not response.content.startswith(b'PK'):
            logger.error(f"Downloaded content is not a valid Excel/ZIP file (detected: {response.content[:20]})")
            if b'<html' in response.content.lower() or b'<!doctype html' in response.content.lower():
                logger.error("Detected HTML content instead of Excel. This likely indicates an error/login page.")
            return None

        excel_bytes = io.BytesIO(response.content)
        sheets = pd.read_excel(excel_bytes, sheet_name=None, engine="openpyxl")

        if sheets:
            logger.info(f"✅ Successfully parsed Excel file with {len(sheets)} sheets")
        else:
            logger.warning("Excel file parsed but contains no sheets")

        return sheets

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error downloading from Azure Graph API: {e}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Error downloading from Azure Graph API: {e}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return None
