
from Tools.GetDependencies import get_dependencies
import json
import streamlit as st

class_name = input("Enter the ABAP class name: ")

dependencies = get_dependencies(class_name=class_name)
print(json.dumps(dependencies, indent=4))