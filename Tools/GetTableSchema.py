from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests
from requests.auth import HTTPBasicAuth
from langchain_core.callbacks import CallbackManagerForToolRun


class GetTableSchemaInput(BaseModel):
    """This is Filter Criteria for the API which will be fetching the table schema based on table_name and field_names (optional)."""

    table_name: str = Field(description="DB Table Name")
    field_names: Optional[List[str]] = Field(
        description="List of Fields to be filtered"
    )
    # system_id: str = Field(
    #     description="System ID for the API Call. List of allowed values:['DHA', 'D2A', 'RHA' ]"
    # )
    # user_name: str = Field(description="User Name for the Basic Auth of API Call")
    # password: str = Field(description="Password for the Basic Auth of API Call")


class GetTableSchema(BaseTool):  # type: ignore[override, override]
    """This tool will be fetching the table schema based on table_name and field_names(optional)"""

    name: str = "get_table_schema"
    description: str = (
        """Fetches the table schema and returns an JSON output like below: 
        {
            "@odata.context" : "$metadata#TabFields(fieldname,keyflag,datatype,leng,decimals,description,tableName)",
            "@odata.metadataEtag" : "W/\"20250118000644\"",
            "value" : [
                {
                "tableName" : "ZDT_SOM_HEADCUST",
                "fieldname" : "REFOBJKEY",
                "keyflag" : true,
                "datatype" : "CHAR",
                "leng" : "10",
                "decimals" : "0",
                "description" : ""
                }
            ]
        }
        """
    )
    args_schema: Type[BaseModel] = GetTableSchemaInput
    return_direct: bool = False

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> Dict[str, Any]:

        # Extract parameters from kwargs if they are passed dynamically
        table_name = kwargs.get("table_name")
        field_names = kwargs.get("field_names")

        system_id = kwargs.get("system_id", "RHA").upper()
        user_name = kwargs.get("user_name", "vaibhago")
        password = kwargs.get("password", "Aichusiddhu123$$")

        if not table_name:
            raise ValueError("Please provide the `table_name`.")

        # Define system mappings
        system_config = {
            "RHA": {
                "hostname": "https://saphec-preprod.cisco.com:44300",
                "sap_client": 300,
            },
            "D2A": {
                "hostname": "https://saphec-dv2.cisco.com:44300",
                "sap_client": 110,
            },
            "DHA": {
                "hostname": "https://saphec-dev.cisco.com:44300",
                "sap_client": 110,
            },
        }

        if system_id not in system_config:
            raise ValueError(
                f"Invalid system_id: {system_id}. Allowed values: {list(system_config.keys())}"
            )

        filters=""
        
        # Construct the fieldname filter dynamically
        if isinstance(field_names, list) and field_names:
            fieldname_filter = " or ".join(
                [f"fieldname eq '{field}'" for field in field_names]
            )
            filters = fieldname_filter
        else:
            filters = "keyflag eq true"  # Fetch only the key fields

        hostname = system_config[system_id]["hostname"]
        sap_client = system_config[system_id]["sap_client"]

        base_url = f"{hostname}/sap/opu/odata4/sap/zsb_table_schema/srvd_a2x/sap/zsd_table_schema/0001/TabFields"

        # Construct the full API URL with filters
        url = (
            f"{base_url}?"
            f"$filter=(tableName eq '{table_name}' and ({filters}))"
            f"&sap-client={sap_client}"
        )

        try:
            # Make the request with authentication
            response = requests.get(
                url, auth=HTTPBasicAuth(user_name, password), timeout=10
            )

            # Check for successful response
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error: {response.status_code} - {response.reason}")

        except requests.exceptions.RequestException as error:
            return {(f"Error: {str(error)}")}
