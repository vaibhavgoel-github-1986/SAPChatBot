import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.auth import AuthApiKey
import json

# ✅ Connection Details
WEAVIATE_URL = "weaviatedb-rcdn-dev.cisco.com"
HTTP_PORT = 6380
GRPC_PORT = 6381
API_KEY = "5y2pDkEqtRe1"

def connect_to_weaviate(url, http_port, grpc_port, apikey):
    """🔗 Establishes connection to Weaviate DB."""
    return weaviate.WeaviateClient(
        connection_params=ConnectionParams.from_params(
            http_host=url,
            http_port=http_port,
            http_secure=True,
            grpc_host=url,
            grpc_port=grpc_port,
            grpc_secure=True,
        ),
        additional_config=AdditionalConfig(
            timeout=Timeout(init=30, query=120, insert=120)
        ),
        skip_init_checks=True,
        auth_client_secret=AuthApiKey(apikey),  # ✅ Correct auth usage
    )


# ✅ Use a context manager to handle cleanup
try:
    with connect_to_weaviate(WEAVIATE_URL, HTTP_PORT, GRPC_PORT, API_KEY) as client:
        
        # ✅ Fetch and format collection list
        collections = client.collections.list_all()

        # ✅ Convert Weaviate object to serializable dictionary
        collections_serializable = [
            {
                "name": col["name"],
                "description": getattr(col, "description", "No description available"),
                # "vectorIndexConfig": getattr(col, "vectorIndexConfig", {}),
                # "shardCount": getattr(col, "shardCount", 1)
            }
            for col in collections
        ]

        # ✅ Pretty-print JSON response
        print("📂 Available Collections:")
        print(json.dumps(collections_serializable, indent=2))

except Exception as e:
    print(f"Exception: {e}")
