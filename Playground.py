import json
import pprint
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import streamlit as st
import re
from Utilities.GetClassSourceCode import get_class_source_code

# Retrieve class name from input
class_name = "zcl_som_i017a_reminder_notif" #"zcl_cc_rate_plan"

# Retrieve class source code
class_source_code = get_class_source_code(class_name)

if not class_source_code:
    raise ValueError(
        f"Class '{class_name}' not found or source code retrieval failed."
    )

# Apply regex to extract the class definition only
class_impl_pattern = re.compile(
    r"(?i)class\s+\w+\s+implementation.*?endclass\.", re.IGNORECASE | re.DOTALL
)
class_impl_code = class_impl_pattern.search(class_source_code)

if not class_impl_code:
    raise ValueError(
        f"Class Implementation not found in source code for '{class_name}'."
    )

# Extract methods
# method_pattern = re.compile(
#     r"\bmethod\s+\w+\s+.*?endmethod\.", re.IGNORECASE | re.DOTALL
# )

# method_pattern = re.compile(r"\bMETHOD\s+([\w~]+)\b", re.IGNORECASE)
method_pattern = re.compile(r"^\s*METHOD\s+([\w~]+)\s*\.", re.IGNORECASE | re.MULTILINE)


methods = method_pattern.findall(class_impl_code.group(0))

pprint.pprint(methods)
 
        

