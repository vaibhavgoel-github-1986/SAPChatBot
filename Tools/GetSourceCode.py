from Utilities.RemoveComments import remove_comments
from langchain_core.tools import BaseTool
from DocumentLoaders.Github import GitHubLoader
from typing import Optional, Type
from pydantic import BaseModel, Field


class SourceCodeInput(BaseModel):
    """Input schema for GetSourceCodeTool."""

    object_name: str = Field(
        description="Name of the ABAP object to fetch (e.g., class name)."
    )
    object_type: str = Field(
        description="""
        Type of the ABAP object. 
        Must be one of 'clas' (Class), 'intf' (Interface), 'tabl' (DB Table), 'prog' (Program), or 'ddls' (CDS View)."""
    )
    repo: Optional[str] = Field(
        default="cisco-it-finance/sap-brim-repo",
        description="GitHub repository to fetch the source code from.",
    )
    branch: Optional[str] = Field(
        default="dha-main", description="GitHub repository branch to fetch from."
    )


class GetSourceCode(BaseTool): # type: ignore[override, override]
    """Tool for fetching and cleaning ABAP object source code from a GitHub repository."""

    name: str = "get_source_code"
    description: str = (
        "Fetches the source code of a specified ABAP Object from a GitHub repository and removes comment blocks."
    )
    args_schema: Type[BaseModel] = SourceCodeInput

    def _run(self, **kwargs) -> str:
        """
        Fetch the source code of an ABAP object and remove comments.
        """

        object_name = kwargs.get("object_name")
        object_type = kwargs.get("object_type")
        repo = kwargs.get("repo")
        branch = kwargs.get("branch")

        # Validate object_name
        if not object_name:
            raise ValueError("`object_name` cannot be empty.")

        # Validate object_type
        allowed_types = {"clas", "intf", "tabl", "prog", "ddls"}
        if object_type not in allowed_types:
            raise ValueError(
                f"Invalid object_type '{object_type}'. Must be one of {allowed_types}"
            )

        # Load source code from GitHub
        github_loader = GitHubLoader(repo=repo, branch=branch)
        document = github_loader.load_files(
            file_filter=lambda file_path: file_path
            == f"zs4intcpq/{object_name.lower()}.{object_type.lower()}.abap",
        )

        if not document:
            raise ValueError(
                f"Object {object_name}/{object_type} was not found in the repository."
            )

        # Remove comments and return cleaned source code
        return remove_comments(document[0].page_content)