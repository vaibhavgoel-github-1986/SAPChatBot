from Utilities.RemoveComments import remove_comments
from DocumentLoaders.LoadGithubFile import load_github_files
from langchain_core.tools import tool

@tool
def get_class_source_code(
    class_name: str,
    repo: str = "cisco-it-finance/sap-brim-repo",
    branch: str = "dha-main",
):  
    """
    Fetches the source code of a specified ABAP class from a GitHub repository and removes comments from it.
    Args:
        class_name (str): The name of the ABAP class whose source code is to be fetched.
        branch (str, optional): The branch of the GitHub repository to fetch the source code from. Defaults to "dha-main".
    Returns:
        str: The cleaned source code of the specified ABAP class with comments removed.
    """
    
    if not class_name:
        raise ValueError("`class_name` cannot be empty.")
    
    document = load_github_files(
        repo=repo,
        branch=branch,
        file_filter=lambda file_path: file_path == f"zs4intcpq/{class_name.lower()}.clas.abap",
    )

    if not document:
        raise ValueError(f"Class '{class_name}' not found in the repository.")
    
    cleaned_code = remove_comments(document[0].page_content)

    return cleaned_code
