import pprint
import requests
from requests.auth import HTTPBasicAuth

class SAPTableSchemaFetcher:
    """
    A class to fetch schema details of an SAP table from OData V4.
    """

    def __init__(self, hostname: str, username: str, password: str, sap_client: str = "300"):
        """
        Initialize API connection settings.
        
        :param hostname: SAP OData service base URL.
        :param username: SAP username.
        :param password: SAP password.
        :param sap_client: SAP client ID (default is '300').
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.sap_client = sap_client
        self.base_url = f"{self.hostname}/sap/opu/odata4/sap/zsb_table_schema/srvd_a2x/sap/zsd_table_schema/0001/TabFields"

    def get_table_fields(self, table_name: str, field_names: list):
        """
        Fetch specific fields for a given SAP table.

        :param table_name: SAP table name.
        :param field_names: List of field names to filter.
        :return: JSON response containing selected table fields.
        """
        if not field_names:
            raise ValueError("Field names list cannot be empty!")

        # Construct the fieldname filter dynamically
        fieldname_filter = " or ".join([f"fieldname eq '{field}'" for field in field_names])

        # Construct the full API URL with filters
        url = (
            f"{self.base_url}?"
            f"$filter=(tableName eq '{table_name}' and ({fieldname_filter}))" 
            f"&sap-client={self.sap_client}"
        )

        try:
            # Make the request with authentication
            response = requests.get(url, auth=HTTPBasicAuth(self.username, self.password), timeout=10)

            # Check for successful response
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error: {response.status_code} - {response.reason}")

        except requests.exceptions.RequestException as error:
            print(f"Error fetching table fields: {error}")
            return None

    def fetch_and_print_fields(self, table_name: str, field_names: list):
        """
        Fetches and prints the filtered fields for a table.

        :param table_name: SAP table name.
        :param field_names: List of field names to filter.
        """
        schema = self.get_table_fields(table_name, field_names)
        if schema:
            pprint.pprint(schema)
        else:
            pprint.pprint("Failed to fetch fields.")

# Usage Example
if __name__ == "__main__":
    fetcher = SAPTableSchemaFetcher(
        hostname="https://saphec-preprod.cisco.com:44300",
        username="vaibhago",
        password="Aichusiddhu123$$"
    )

    table_name = "ZDT_SOM_HEADCUST"
    field_names = ["MANDT", "REFOBJKEY"]
    
    fetcher.fetch_and_print_fields(table_name, field_names)
