from Utilities.GetClassSourceCode import get_interface_source_code
from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class InterfaceDefinitionInput(BaseModel):
    """Input schema for GetSourceCodeTool."""

    interface_name: str = Field(
        description="Name of the Interface object to fetch (e.g., zif_*)."
    )


class GetInterfaceDefinition(BaseTool):  # type: ignore[override, override]
    """Tool for fetching and cleaning ABAP Interface object source code from a GitHub repository."""

    name: str = "get_interface_definition"
    description: str = (
        "Fetches the source code of a specified ABAP Interface Object from a GitHub repository and removes comment blocks."
    )
    args_schema: Type[BaseModel] = InterfaceDefinitionInput

    def _run(self, **kwargs) -> str:
        """
        Fetch the source code of an ABAP object and remove comments.
        """

        # Parse input using Pydantic to get default values
        input_data = InterfaceDefinitionInput.model_validate(kwargs)

        interface_name = input_data.interface_name

        # Validate object_name
        if not interface_name:
            raise ValueError("`interface_name` cannot be empty.")

        # Retrieve class source code
        interface_source_code = get_interface_source_code(interface_name)

        if interface_source_code:
            return interface_source_code
        else:
            raise ValueError(
                f"Failed to get the source code for Interface: '{interface_source_code}'."
            )
