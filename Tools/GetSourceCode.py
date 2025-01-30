from Tools.RemoveComments import remove_comments
from langchain_core.tools import tool
from DocumentLoaders.Github import GitHubLoader

@tool
def get_source_code(
    object_name: str,
    object_type: str,
    repo: str = "cisco-it-finance/sap-brim-repo",
    branch: str = "dha-main",
):
    """
    Fetches the source code of a specified ABAP Object from a GitHub repository and removes comment blocks from it.
    Args:
        object_name (str): The name of the ABAP class whose source code is to be fetched.
        object_type (str): The type of the ABAP object to fetch.
        Values can be one of "clas" - Class, "intf" - Interface, "tabl" - DB Table, "prog" - Program, "ddls" - CDS View.
        repo (str, optional): The GitHub repository to fetch the source code from. Defaults to "cisco-it-finance/sap-brim-repo".
        branch (str, optional): The branch of the GitHub repository to fetch the source code from. Defaults to "dha-main".
    Returns:
        str: The cleaned source code of the specified ABAP class with comments removed.
    """

    if not object_name:
        raise ValueError("`object_name` cannot be empty.")

    allowed_types = {"clas", "intf", "tabl", "prog", "ddls"}
    if object_type not in allowed_types:
        raise ValueError(
            f"Invalid object_type '{object_type}'. Must be one of {allowed_types}"
        )

    github_loader = GitHubLoader(repo=repo, branch=branch)
    
    document = github_loader.load_files(
        file_filter=lambda file_path: file_path
        == f"zs4intcpq/{object_name.lower()}.{object_type.lower()}.abap",
    )

    if not document:
        raise ValueError(f"Object {object_name}/{object_type} was not found in the repository.")

    cleaned_code = remove_comments(document[0].page_content)

    return cleaned_code
