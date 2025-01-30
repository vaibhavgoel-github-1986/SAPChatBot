
from Utilities.GetDependencies import get_dependencies
import json
import streamlit as st

class_name = input("Enter the ABAP class name: ")  #zcl_cc_rate_plan

dependencies = get_dependencies(class_name=class_name)
print(json.dumps(dependencies, indent=4))  