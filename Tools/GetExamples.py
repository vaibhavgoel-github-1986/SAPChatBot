from Utilities.RemoveComments import remove_comments
from langchain_core.tools import BaseTool
from DocumentLoaders.Github import GitHubLoader
from typing import Type
from pydantic import BaseModel, Field
from pathlib import Path
import os

class GetExamplesInput(BaseModel):
    """Input schema for GetSourceCodeTool."""

    test_double_type: str = Field(
        description="""
            Type of test double framework.
            Allowed values: ["sql", "cds", "ooabap", "func", "authcheck", "testseams"]
        """
    )


class GetExamples(BaseTool):  # type: ignore[override, override]
    """Tool for fetching and cleaning ABAP object source code from a GitHub repository."""

    name: str = "get_test_double_examples"
    description: str = "Fetches the examples for the required test double framework"
    args_schema: Type[BaseModel] = GetExamplesInput

    def _run(self, **kwargs) -> str:
        """
        Fetches the examples for the required test double framework
        """

        test_double_type = str(kwargs.get("test_double_type", "")).lower().strip()

        # Validate test_double_type
        allowed_types = {"sql", "cds", "ooabap", "func", "authcheck", "testseams"}
        if test_double_type not in allowed_types:
            raise ValueError(
                f"Invalid test_double_type: '{test_double_type}'. Allowed values: {allowed_types}"
            )

        # Get the absolute base directory
        BASE_DIR = Path(__file__).resolve().parent

        # Define file mappings with absolute paths
        file_mapping = {
            "sql": BASE_DIR / "Examples/SQLTestDouble.py",
            "cds": BASE_DIR / "Examples/CDSTestDouble.py",
            "ooabap": BASE_DIR / "Examples/OO-AbapTestDouble.py",
            "func": BASE_DIR / "Examples/FuncModuleTestDouble.py",
            "authcheck": BASE_DIR / "Examples/AuthCheckController.py",
            "testseams": BASE_DIR / "Examples/TestSeams.py",
        }

        # Get the file path
        file_path = file_mapping[test_double_type]

        # Ensure file exists and is accessible
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK):  # Check read permissions
            raise PermissionError(f"Permission denied: {file_path}")

        # Read and return the file content
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"
