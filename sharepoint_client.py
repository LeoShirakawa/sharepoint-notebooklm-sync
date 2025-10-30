
import os
import msal
import requests
import config

# The base URL for Microsoft Graph API
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

_app = None
_drive_id = None # Cache for the drive ID

def _get_msal_app():
    """Initializes and returns the MSAL ConfidentialClientApplication instance."""
    global _app
    if not _app:
        _app = msal.ConfidentialClientApplication(
            client_id=config.SHAREPOINT_CLIENT_ID,
            authority=config.SHAREPOINT_AUTHORITY,
            client_credential=os.environ.get("SHAREPOINT_CLIENT_SECRET"), # Read from environment variable
        )
    return _app

def get_graph_access_token():
    """
    Acquires an access token for Microsoft Graph API.

    Returns:
        str: The access token, or None if acquisition fails.
    """
    app = _get_msal_app()
    result = app.acquire_token_silent(scopes=config.SHAREPOINT_SCOPE, account=None)

    if not result:
        print("No suitable token exists in cache, acquiring a new one from AAD")
        result = app.acquire_token_for_client(scopes=config.SHAREPOINT_SCOPE)

    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"Failed to acquire token: {result.get('error_description')}")
        return None

def _get_drive_id(token):
    """Internal function to get and cache the drive ID of the SharePoint document library."""
    global _drive_id
    if _drive_id:
        return _drive_id

    _drive_id = config.SHAREPOINT_DRIVE_ID
    print(f"SharePoint: Using configured Drive ID: {_drive_id}")
    return _drive_id

def list_files():
    """
    Lists all files in the configured SharePoint folder.

    Returns:
        list: A list of file metadata objects, or an empty list on failure.
    """
    token = get_graph_access_token()
    if not token:
        print("Could not get Graph API token. Aborting list_files.")
        return []

    drive_id = _get_drive_id(token)
    if not drive_id:
        return []

    # List children of the specific folder item within the drive
    folder_children_url = f"{GRAPH_API_BASE_URL}/drives/{drive_id}/items/{config.SHAREPOINT_FOLDER_ID}/children"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"SharePoint: Requesting URL: {folder_children_url}") # Debug log
    files_response = requests.get(folder_children_url, headers=headers)

    if files_response.status_code != 200:
        print(f"SharePoint: Error listing files: {files_response.status_code} {files_response.text}") # Detailed error log
        return []

    files = files_response.json().get("value", [])
    print(f"Found {len(files)} items in the SharePoint folder.")
    return files

def download_file_content(file_id: str):
    """
    Downloads the content of a specific file.

    Returns:
        bytes: The raw content of the file, or None on failure.
    """
    token = get_graph_access_token()
    if not token:
        print("Could not get Graph API token. Aborting download.")
        return None

    drive_id = _get_drive_id(token)
    if not drive_id:
        return None

    file_content_url = f"{GRAPH_API_BASE_URL}/drives/{drive_id}/items/{file_id}/content"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"SharePoint: Requesting URL: {file_content_url}") # Debug log
    response = requests.get(file_content_url, headers=headers)

    if response.status_code == 200:
        return response.content
    else:
        print(f"SharePoint: Error downloading file content: {response.status_code} {response.text}") # Detailed error log
        return None
