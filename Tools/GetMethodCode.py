from typing import List, Optional, Tuple, Type
import re
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from Utilities.GetClassSourceCode import get_class_source_code


class MethodCodeInput(BaseModel):
    """Input for the GetClassDefinition tool."""

    class_name: str = Field(
        description="SAP ABAP Class Name, usually starts with ZCL_* or zcl_* pattern."
    )
    meth_name: str = Field(description="Method Name to fetch the code for.")


class GetMethodCode(BaseTool):  # type: ignore[override, override]
    """Tool that fetches the source code for a specific Method in a Class."""

    name: str = "get_method_code"
    description: str = (
        "Fetches the fetches the source code for a specific Method in a Class."
    )
    args_schema: Type[BaseModel] = MethodCodeInput
    return_direct: bool = False

    def _run(self, **kwargs) -> str:
        """
        Fetches the class definition and method signatures from an ABAP Class.
        Removes TYPES, DATA, CONSTANTS, and other non-essential parts.
        """

        # Retrieve class name from input
        class_name = kwargs.get("class_name")
        meth_name = kwargs.get("meth_name")

        if not class_name:
            raise ValueError("`class_name` cannot be empty.")

        if not meth_name:
            raise ValueError("`meth_name` cannot be empty.")

        # Retrieve class source code
        class_source_code = get_class_source_code(class_name)

        if not class_source_code:
            raise ValueError(
                f"Class '{class_name}' not found or source code retrieval failed."
            )

        # Extract method body
        method_body_pattern = re.compile(
            rf"METHOD\s+(?:\w+~)?{meth_name}\b.*?ENDMETHOD", re.IGNORECASE | re.DOTALL
        )

        method_code = method_body_pattern.search(class_source_code)

        if method_code:
            return method_code.group(0)
        else:
            raise ValueError(
                f"Failed to extract source code for the method: {meth_name}."
            )
