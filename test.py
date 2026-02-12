from client import CodeCarbonApiClient
from pathlib import Path
import json

def get_access_token_from_file() -> str:
    cred_path = Path(".credentials.json")
    with cred_path.open("r") as f:
        data = json.load(f)
    return data["tokens"]["access_token"]

client = CodeCarbonApiClient(
    base_url="https://api.codecarbon.io",
    access_token=get_access_token_from_file()
)

print(client.check_auth()) 
print(client.list_organizations())  
