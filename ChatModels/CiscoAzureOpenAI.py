import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from ChatModels.TokenManager import TokenManager
from typing import Optional
import streamlit as st

# Load environment variables from .env file
load_dotenv()
        
class CiscoAzureOpenAI:
    def __init__(
        self,
        deployment_name: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        app_key: Optional[str] = None,
        user_id: Optional[str] = None,
        token_manager: Optional[TokenManager] = None,
    ):
        """
        Initializes the CiscoAzureOpenAI class.

        Args:
            deployment_name (str): The Azure deployment name. Defaults to the value from the environment variable `DEPLOYMENT_NAME`.
            azure_endpoint (str): The Azure API endpoint. Defaults to the value from the environment variable `AZURE_ENDPOINT`.
            api_version (str): The Azure API version. Defaults to the value from the environment variable `AZURE_API_VERSION`.
            app_key (str): The application key. Defaults to the value from the environment variable `CISCO_APP_KEY`.
            user_id (str): The user ID. Defaults to the value from the environment variable `CISCO_USER_ID`.
            token_manager (TokenManager): An instance of the TokenManager for handling tokens. Must be provided.
        """

        self.deployment_name = deployment_name or st.secrets["AZURE_DEPLOYMENT_NAME"] 
        self.azure_endpoint = azure_endpoint or st.secrets["AZURE_ENDPOINT"]
        self.api_version = api_version or st.secrets["AZURE_API_VERSION"]
        self.app_key = app_key or st.secrets["CISCO_APP_KEY"]
        self.user_id = user_id or st.secrets["CISCO_USER_ID"]
        self.token_manager = token_manager

        if not all(
            [
                self.deployment_name,
                self.azure_endpoint,
                self.api_version,
                self.app_key,
                self.user_id,
            ]
        ):
            raise ValueError(
                "Missing required parameters. Ensure `deployment_name`, `azure_endpoint`, `api_version`, `app_key`, "
                "and `user_id` are provided or set in environment variables."
            )
        if not self.token_manager:
            raise ValueError("A valid TokenManager instance must be provided.")

        self.llm = None

    def get_llm(self):
        """
        Retrieves an instance of AzureChatOpenAI configured with the required parameters.

        Returns:
            AzureChatOpenAI: The AzureChatOpenAI instance.

        Raises:
            ValueError: If the token retrieval fails.
        """
        if not self.llm:
            api_key = self.token_manager.get_auth_token()
            if not api_key:
                raise ValueError("Failed to retrieve Cisco token.")
            self.llm = AzureChatOpenAI(
                deployment_name=self.deployment_name,
                azure_endpoint=self.azure_endpoint,
                api_key=api_key,
                api_version=self.api_version,
                verbose=True,
                temperature=0.2,
                model_kwargs={
                    "user": f'{{"appkey": "{self.app_key}", "user": "{self.user_id}"}}'
                },
            )
        return self.llm
