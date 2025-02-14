import time
import requests
import base64
import os
import traceback
import streamlit as st
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ Global variables for token caching
_cached_token = None
_token_expiry = 0  # Stores token expiry time (UNIX timestamp)


def get_auth_token(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    token_url: Optional[str] = None,
) -> Optional[str]:
    """
    Fetches an authentication token using client credentials.
    Automatically refreshes the token if it is expired.

    Args:
        client_id (str): The client ID for authentication. Defaults to `CISCO_CLIENT_ID` from Streamlit secrets or environment.
        client_secret (str): The client secret for authentication. Defaults to `CISCO_CLIENT_SECRET` from Streamlit secrets or environment.
        token_url (str): The URL for token generation. Defaults to `CISCO_TOKEN_URL` from Streamlit secrets or environment.

    Returns:
        str: The access token if successfully retrieved, None otherwise.
    """
    global _cached_token, _token_expiry

    # ✅ Check if cached token is still valid
    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    # ✅ Fetch credentials from Streamlit secrets or environment
    client_id = (
        client_id or st.secrets.get("CISCO_CLIENT_ID") or os.getenv("CISCO_CLIENT_ID")
    )
    client_secret = (
        client_secret
        or st.secrets.get("CISCO_CLIENT_SECRET")
        or os.getenv("CISCO_CLIENT_SECRET")
    )
    token_url = (
        token_url or st.secrets.get("CISCO_TOKEN_URL") or os.getenv("CISCO_TOKEN_URL")
    )

    if not all([client_id, client_secret, token_url]):
        raise ValueError(
            "Missing required parameters. Ensure `client_id`, `client_secret`, and `token_url` are set."
        )

    payload = "grant_type=client_credentials"
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}",
    }

    try:
        response = requests.post(token_url, headers=headers, data=payload)
        response.raise_for_status()
        response_data = response.json()

        # ✅ Store the new token and expiry time
        _cached_token = response_data.get("access_token")
        expires_in = response_data.get(
            "expires_in", 3600
        )  # Default to 1 hour if not provided
        _token_expiry = time.time() + expires_in - 10  # Buffer of 10 seconds

        return _cached_token

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
        traceback.print_exc()

    return None


def clear_auth_token():
    """
    Clears the cached authentication token.
    """
    global _cached_token, _token_expiry
    _cached_token = None
    _token_expiry = 0
