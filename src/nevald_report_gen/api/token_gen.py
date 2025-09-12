# =================================================================================
# This script generates a VALD Hub access token using the enviorment credentials
# Returns a string with the access token
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import os
import requests
import json
from datetime import datetime, timedelta


# -- ENVIORMENT VARIABLES ---------------------------------------------------------

from nevald_report_gen.config import VALD_CLIENT_ID, VALD_CLIENT_SECRET, VALD_AUTH_URL, TOKEN_CACHE_FILE

CLIENT_ID     = VALD_CLIENT_ID
CLIENT_SECRET = VALD_CLIENT_SECRET
AUTH_URL      = VALD_AUTH_URL
CACHE_FILE    = TOKEN_CACHE_FILE

# -- TOKEN GENERATION FUNCTION ---------------------------------------------------
def get_vald_token():
    # Check cache for existing token
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            if datetime.now() < datetime.fromisoformat(data["expires_at"]):
                return data["access_token"]
            
    # If no cache or expired, generate new token
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(AUTH_URL, data=payload)
    if response.status_code == 200:
        token = response.json()['access_token']
        expires_in = response.json().get('expires_in', 7200)
        expires_at = (datetime.now() + timedelta(seconds=expires_in - 60)).isoformat()

        with open(CACHE_FILE, "w") as f:
            json.dump({"access_token": token, "expires_at": expires_at}, f)

        print("Access token refreshed.")
        return token
    else:
        raise Exception(f"Auth failed: {response.status_code} - {response.text}")

