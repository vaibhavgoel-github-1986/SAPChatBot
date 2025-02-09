from typing import List, Type
import re
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from Utilities.GetClassSourceCode import get_class_source_code

class MethodListOutput(BaseModel):
    """Structured output containing method details for a given ABAP class."""
    
    class_name: str = Field(..., description="The name of the SAP ABAP class.")
    methods: List[str] = Field(..., description="List of methods implemented in the class.")


class MethodListInput(BaseModel):
    """Input for the GetClassDefinition tool."""

    class_name: str = Field(
        description="SAP ABAP Class Name, usually starts with ZCL_* or zcl_* pattern."
    )


class GetMethodList(BaseTool):  # type: ignore[override, override]
    """Tool that fetches the class definition and method signatures from a specified ABAP Class."""

    name: str = "get_method_list"
    description: str = "Fetches the implemented methods in a class definition"
    args_schema: Type[BaseModel] = MethodListInput 
    return_direct: bool = False

    def _run(self, **kwargs) -> MethodListOutput: #List[str]:
        """
        Fetches the class definition and method signatures from an ABAP Class.
        Removes TYPES, DATA, CONSTANTS, and other non-essential parts.
        """

        # Retrieve class name from input
        class_name = kwargs.get("class_name")

        if not class_name:
            raise ValueError("`class_name` cannot be empty.")

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
        method_pattern = re.compile(
            r"^\s*METHOD\s+([\w~]+)\s*\.", re.IGNORECASE | re.MULTILINE
        )

        methods = method_pattern.findall(class_impl_code.group(0))
        methods = [method.lower() for method in methods]

        if methods:
            return MethodListOutput(class_name=class_name, methods=methods) 
            # return methods
        else:
            raise ValueError(f"Methods not found in source code for '{class_name}'.")
