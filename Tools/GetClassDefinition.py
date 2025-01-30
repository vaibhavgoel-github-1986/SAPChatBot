from Tools.RemoveComments import remove_comments
from langchain_core.tools import tool
from DocumentLoaders.Github import GitHubLoader

import re

from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper

@tool
def extract_class_definition(abap_code):
    """
    Extracts the class definition and method signatures from ABAP source code.
    Removes TYPES, DATA, CONSTANTS, and other non-essential parts.
    Case-insensitive filtering for sections.
    """
    lines = abap_code.split("\n")
    trimmed_lines = []
    keep_line = False

    for line in lines:
        original_line = line.strip()  # Preserve original case for output
        lower_line = original_line.lower()  # Convert to lowercase for comparison

        # Keep class definition
        if lower_line.startswith("class ") and "definition" in lower_line:
            keep_line = True
            trimmed_lines.append(original_line)
            continue

        # Ignore TYPES, DATA, CONSTANTS, CLASS-DATA
        if any(
            keyword in lower_line
            for keyword in ["macro", "types", "data", "class-data", "constants"]
        ):
            keep_line = False  # Ignore until a new relevant section starts
            continue

        # Keep section headers (case insensitive)
        if lower_line in ["public section.", "protected section.", "private section."]:
            keep_line = True
            trimmed_lines.append(original_line)
            continue

        # Keep only METHOD and CLASS-METHODS declarations (case insensitive)
        if lower_line.startswith("methods") or lower_line.startswith("class-methods"):
            keep_line = True  # Resume keeping lines for method definitions
            trimmed_lines.append(original_line)
            continue

        # Ignore anything else when keep_line is False
        if keep_line:
            trimmed_lines.append(original_line)

    return "\n".join(trimmed_lines)

