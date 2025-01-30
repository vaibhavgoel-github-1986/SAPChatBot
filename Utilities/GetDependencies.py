import re
from typing import Dict, List
from Utilities.GetClassSourceCode import get_class_source_code
from Utilities.RemoveComments import remove_comments
from langchain_core.tools import tool

def extract_table_names(method_body: str) -> List[str]:
    """
    Extracts table names from SAP ABAP SELECT queries in the given class code.

    Args:
        class_code: The ABAP class code as a string.

    Returns:
        A list of table names used in the SELECT queries, ensuring uniqueness and maintaining order.
    """
    # Regex to capture SELECT queries and table names
    # select_query_pattern = re.compile(
    #     r"SELECT\s+.*?\s+FROM\s+.*?(?=INTO|WHERE|ORDER|GROUP|END|$)",
    #     re.IGNORECASE | re.DOTALL,
    # )

    select_query_pattern = re.compile(
        r"\bSELECT\b.*?\bFROM\b.*?(?=\bINTO\b|\bWHERE\b|\bORDER\b|\bGROUP\b|\bHAVING\b|\bENDSELECT\b|$)",
        re.IGNORECASE | re.DOTALL
    )
    # Regex to extract tables after FROM or any type of JOIN
    # table_pattern = re.compile(
    #     r"(?:FROM|JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|OUTER\s+JOIN|LEFT\s+OUTER\s+JOIN|RIGHT\s+OUTER\s+JOIN)\s+([a-zA-Z0-9_/\~]+)(?=\s+|$)",
    #     re.IGNORECASE
    # )

    table_pattern = re.compile(
        r"(?i)\b(?:FROM|(?:(?:LEFT|RIGHT|FULL|INNER|CROSS)\s*(?:OUTER\s*)?)?JOIN)\s+([A-Za-z0-9_]+)",
        re.IGNORECASE
    )
    
    # To maintain the order and uniqueness:
    seen_tables = set()
    ordered_tables = []

    # Find all SELECT queries
    for match in select_query_pattern.finditer(method_body):
        query = match.group(0).strip()  # Extract the entire SELECT query

        # Extract table names that appear after FROM or JOIN
        tables_in_query = table_pattern.findall(query)
        for tbl in tables_in_query:
            table_upper = tbl.upper()  # or keep original case if you prefer
            if table_upper not in seen_tables:
                seen_tables.add(table_upper)
                ordered_tables.append(table_upper)
        
    return ordered_tables

def extract_class_references(method_body: str) -> List[str]:
    """
    Extracts class references (instantiations and static calls)
    from SAP ABAP code in the given method body.

    Args:
        method_body: The ABAP method code as a string.

    Returns:
        A list of unique class names (in uppercase), preserving the order of first appearance.
    """
    # 1) Pattern for object instantiations:
    #    - CREATE OBJECT lo_obj TYPE CL_FOO
    #    - DATA(lo_obj) = NEW ZCL_BAR( )
    #    - NEW CL_BAZ( )
    instantiation_pattern = re.compile(
        r"\b(?:CREATE\s+OBJECT\s+\w+\s+TYPE\s+|CREATE\s+OBJECT\s+|DATA\s*\(\w+\)\s*=\s*NEW\s+|NEW\s+)(CL_\w+|ZCL_\w+)",
        re.IGNORECASE
    )

    # 2) Pattern for static method calls:
    #    - cl_salv_table=>factory( ... )
    #    - zcl_custom=>do_something( ... )
    #    - Possibly with or without spaces, e.g. "CL_FOO => method("
    #      or "CL_FOO=>method("
    static_call_pattern = re.compile(
        r"\b(CL_\w+|ZCL_\w+)\s*=>\s*\w+\s*\(",
        re.IGNORECASE
    )

    # Find all classes from instantiations
    instantiations = instantiation_pattern.findall(method_body)

    # Find all classes from static calls
    static_calls = static_call_pattern.findall(method_body)

    # Combine both lists
    all_classes = instantiations + static_calls

    # Remove duplicates while preserving order
    seen = set()
    ordered_unique = []
    for class_name in all_classes:
        uc_name = class_name.upper()
        if uc_name not in seen:
            seen.add(uc_name)
            ordered_unique.append(uc_name)

    return ordered_unique

@tool
def get_dependencies(class_name: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Returns JSON Schema for dependencies in a class

    Args:
        class_name (str): Class Name

    Returns:
        A JSON Schema for dependencies in a class
    """
    if not class_name:
        raise ValueError("Please provide a `class_name`.")
    
    class_code = get_class_source_code(class_name)

    class_code = remove_comments(class_code)
    
    dependencies = {
        "interfaces": [],
        "methods": {},
    }

    # Extract interfaces
    interface_pattern = re.compile(r"\bINTERFACES\s+(\w+)", re.IGNORECASE)
    dependencies["interfaces"] = [interface.upper() for interface in interface_pattern.findall(class_code)]

    # Extract methods
    method_pattern = re.compile(r"\b[Mm]ETHOD\s+([/\w~]+)\s*\.", re.IGNORECASE)
    methods = [method.upper() for method in method_pattern.findall(class_code)]

    for method in methods:
        dependencies["methods"][method] = {
            "codelines": 0,
            "tables": [],
            "function_modules": [],
            "classes": [],
            "source_code": "",
        }

        # Extract method body
        method_body_pattern = re.compile(
            r"METHOD\s+" + method + r".*?ENDMETHOD", re.IGNORECASE | re.DOTALL
        )
        method_body = method_body_pattern.search(class_code).group()
        dependencies["methods"][method]["source_code"] = method_body
        
        # Count lines of ABAP code in the method body, excluding blank lines
        code_lines = [line for line in method_body.splitlines() if line.strip()]
        dependencies["methods"][method]["codelines"] = len(code_lines)

        # Extract tables being used in SELECT queries 
        dependencies["methods"][method]["tables"] = extract_table_names(method_body)

        # Extract function modules
        function_pattern = re.compile(r"CALL\s+FUNCTION\s+'(\w+)'", re.IGNORECASE)
        
        function_modules = [function.upper() for function in function_pattern.findall(method_body)]
        dependencies["methods"][method]["function_modules"] = list(set(function_modules))

        # Extract class instantiations and static method calls
        dependencies["methods"][method]["classes"] = extract_class_references(method_body)   

    return dependencies

