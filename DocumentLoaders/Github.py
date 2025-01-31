import os
from typing import List, Optional, Callable

from dotenv import load_dotenv
from langchain_community.document_loaders import GithubFileLoader
from langchain.schema import Document
import streamlit as st

# Load environment variables from .env file
load_dotenv()


class GitHubLoader:
    """
    A utility class for loading documents from GitHub repositories.
    Supports loading individual files and entire directories, including filtering and custom API URLs.
    """

    def __init__(
        self,
        repo: str,
        branch: str = "main",
        github_token: str = st.secrets["CISCO_GITHUB_TOKEN"],
        github_api_url: str = "https://api.github.com",
    ):
        """
        Initializes the GitHubLoader.

        Args:
            repo: The GitHub repository in "owner/repo" format.
            branch: The branch to load from (default: "main").
            github_token: GitHub personal access token.  If not provided, it attempts to use the `GITHUB_TOKEN` environment variable.
            github_api_url: The base URL for the GitHub API.  Defaults to the public GitHub API.
        Raises:
            ValueError: If `repo` is empty or a GitHub token is not provided.
        """

        if not repo:
            raise ValueError("`repo` cannot be empty.")

        self.repo = repo
        self.branch = branch
        self.github_token = github_token
        self.github_api_url = github_api_url

    def load_files(
        self, file_filter: Optional[Callable[[str], bool]] = None
    ) -> List[Document]:
        """Loads a single file from the GitHub repository, optionally applying a file filter."""

        loader = GithubFileLoader(
            repo=self.repo,
            branch=self.branch,
            access_token=self.github_token,
            github_api_url=self.github_api_url,
            file_filter=file_filter,
        )
        return loader.load()
