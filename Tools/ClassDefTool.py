from typing import List, Optional, Tuple, Type
import re
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from Utilities.GetClassSourceCode import get_class_source_code


class ClassDefinitionInput(BaseModel):
    """Input for the GetClassDefinition tool."""

    class_name: str = Field(
        description="SAP ABAP Class Name, usually starts with ZCL_* or zcl_* pattern."
    )


class ClassDefTool(BaseTool):  # type: ignore[override, override]
    """Tool that fetches the class definition and method signatures from a specified ABAP Class."""

    name: str = "get_class_definition"
    description: str = (
        "Fetches the class definition and method signatures from a specified ABAP Class."
    )
    args_schema: Type[BaseModel] = ClassDefinitionInput
    response_format: str = "content_and_artifact"
    return_direct: bool = False

    def _run(self, **kwargs) -> str:
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
        class_definition_pattern = re.compile(
            r"(?i)class\s+\w+\s+definition.*?endclass\.", re.IGNORECASE | re.DOTALL
        )
        class_definition_code = class_definition_pattern.search(class_source_code)

        if class_definition_code:
            return (class_definition_code.group(0), class_source_code)
        else:
            raise ValueError(
                f"Class definition not found in source code for '{class_name}'."
            )
