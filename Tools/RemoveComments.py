import re

"""
Remove comment blocks from the provided source code.

This function uses a regular expression to identify and remove blocks of 
comments that consist of three or more consecutive comment lines.

Args:
    source_code (str): The source code from which to remove comment blocks.

Returns:
    str: The cleaned source code with comment blocks removed.
"""
def remove_comments(source_code: str):

    # Define regex to remove comment blocks (3 or more consecutive comment lines)
    regex = r'(?:(?:^\s*[*"].*$\n?){3,})'

    # Apply regex to clean up the code
    cleaned_code = re.sub(regex, "", source_code, flags=re.MULTILINE)

    return cleaned_code
