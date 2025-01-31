import os
from typing import List, Optional, Callable

from dotenv import load_dotenv
from langchain_community.document_loaders import GithubFileLoader
from langchain.schema import Document
import streamlit as st

# Load environment variables from .env file
load_dotenv()

def load_github_files(
    repo: str,
    branch: str = "main",
    github_token: str = st.secrets("CISCO_GITHUB_TOKEN"),
    github_api_url: str = "https://api.github.com",
    file_filter: Optional[Callable[[str], bool]] = None,
) -> List[Document]:
    """
    Loads documents from a GitHub repository, optionally applying a file filter.

    Args:
        repo: The GitHub repository in "owner/repo" format.
        branch: The branch to load from (default: "main").
        github_token: GitHub personal access token. If not provided, it attempts to use the `CISCO_GITHUB_TOKEN` environment variable.
        github_api_url: The base URL for the GitHub API (default: public GitHub API).
        file_filter: An optional callable to filter files by their path.

    Returns:
        A list of Document objects loaded from the GitHub repository.

    Raises:
        ValueError: If `repo` is empty or a GitHub token is not provided.
    """
    if not repo:
        raise ValueError("`repo` cannot be empty.")

    loader = GithubFileLoader(
        repo=repo,
        branch=branch,
        access_token=github_token,
        github_api_url=github_api_url,
        file_filter=file_filter,
    )
    return loader.load()
