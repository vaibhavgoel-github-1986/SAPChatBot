import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import streamlit as st
from typing import Optional
from Utilities.GetAuthToken import (
    get_auth_token,
)

# Load environment variables
load_dotenv()


def get_azure_llm(
    deployment_name: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    api_version: Optional[str] = None,
    app_key: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AzureChatOpenAI:
    """
    Retrieves an instance of AzureChatOpenAI configured with the required parameters.

    Args:
        deployment_name (str): Azure deployment name. Defaults to `AZURE_DEPLOYMENT_NAME` from env.
        azure_endpoint (str): Azure API endpoint. Defaults to `AZURE_ENDPOINT` from env.
        api_version (str): Azure API version. Defaults to `AZURE_API_VERSION` from env.
        app_key (str): Application key. Defaults to `CISCO_APP_KEY` from env.
        user_id (str): User ID. Defaults to `CISCO_USER_ID` from env.

    Returns:
        AzureChatOpenAI: The configured LLM instance.

    Raises:
        ValueError: If required parameters are missing or token retrieval fails.
    """
    # ✅ Fetch values from Streamlit secrets or environment
    deployment_name = (
        deployment_name
        or st.secrets.get("AZURE_DEPLOYMENT_NAME")
        or os.getenv("AZURE_DEPLOYMENT_NAME")
    )
    azure_endpoint = (
        azure_endpoint
        or st.secrets.get("AZURE_ENDPOINT")
        or os.getenv("AZURE_ENDPOINT")
    )
    api_version = (
        api_version
        or st.secrets.get("AZURE_API_VERSION")
        or os.getenv("AZURE_API_VERSION")
    )
    app_key = app_key or st.secrets.get("CISCO_APP_KEY") or os.getenv("CISCO_APP_KEY")
    user_id = user_id or st.secrets.get("CISCO_USER_ID") or os.getenv("CISCO_USER_ID")

    # ✅ Validate required parameters
    if not all([deployment_name, azure_endpoint, api_version, app_key, user_id]):
        raise ValueError(
            "Missing required parameters. Ensure all environment variables are set."
        )

    # ✅ Fetch authentication token
    api_key = get_auth_token()
    if not api_key:
        raise ValueError("Failed to retrieve Cisco authentication token.")

    # ✅ Return the configured LLM instance
    return AzureChatOpenAI(
        deployment_name=deployment_name,
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
        verbose=True,
        temperature=0.2,
        model_kwargs={"user": f'{{"appkey": "{app_key}", "user": "{user_id}"}}'},
    )
