from dotenv import load_dotenv
import requests
import base64
import traceback
import os
from typing import Optional
import streamlit as st

# Load environment variables from a .env file if present
load_dotenv()

class TokenManager:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
    ):
        """
        Initializes the TokenManager.

        Args:
            client_id (str): The client ID for authentication. Defaults to the value from the environment variable `CISCO_CLIENT_ID`.
            client_secret (str): The client secret for authentication. Defaults to the value from the environment variable `CISCO_CLIENT_SECRET`.
            token_url (str): The URL for token generation. Defaults to the value from the environment variable `CISCO_TOKEN_URL`.
        """

        self.client_id = client_id or st.secrets["CISCO_CLIENT_ID"]
        self.client_secret = client_secret or st.secrets["CISCO_CLIENT_SECRET"]
        self.token_url = token_url or st.secrets["CISCO_TOKEN_URL"]
        self.token = None

        # Validate that all required fields are present
        if not all([self.client_id, self.client_secret, self.token_url]):
            raise ValueError(
                "Missing required parameters. Ensure `client_id`, `client_secret`, and `token_url` are provided or set in environment variables."
            )

    def get_auth_token(self) -> Optional[str]:
        """
        Fetches an authentication token using client credentials.

        Returns:
            str: The access token if successfully retrieved, None otherwise.
        """
        if self.token:
            return self.token

        payload = "grant_type=client_credentials"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }

        try:
            response = requests.post(self.token_url, headers=headers, data=payload)
            response.raise_for_status()
            self.token = response.json().get("access_token")
            return self.token
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")
            traceback.print_exc()
        return None

    def clear_token(self):
        """Clears the cached token."""
        self.token = None
