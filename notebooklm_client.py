import os
import json
import time
import requests
import google.auth
from google.oauth2 import credentials
from google.cloud import iam_credentials_v1
import mimetypes
import base64
import urllib.parse

import config

# This base URL is for standard API calls like delete
API_BASE_URL = "https://global-discoveryengine.googleapis.com/v1alpha"

def get_access_token() -> credentials.Credentials:
    """
    Cloud Run環境で、キーファイルなしでDWDユーザー資格情報を生成します。
    IAM Credentials API (signJwt) を使用します。
    """
    try:
        default_creds, project = google.auth.default(scopes=['https://www.googleapis.com/auth/iam'])
        metadata_server_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
        headers = {"Metadata-Flavor": "Google"}
        response = requests.get(metadata_server_url, headers=headers)
        response.raise_for_status()
        sa_email = response.text.strip()
        if not sa_email:
            raise ValueError("Failed to get the default service account email.")
    except Exception as e:
        print(f"Failed to get Cloud Run default credentials: {e}")
        raise

    token_uri = "https://oauth2.googleapis.com/token"
    now = int(time.time())
    expiry = now + 3600

    payload = {
        "iss": config.DELEGATOR_SERVICE_ACCOUNT_EMAIL,
        "sub": config.USER_EMAIL_TO_IMPERSONATE,
        "aud": token_uri,
        "iat": now,
        "exp": expiry,
        "scope": " ".join(config.NOTEBOOKLM_SCOPES),
    }

    try:
        iam_client = iam_credentials_v1.IAMCredentialsClient(credentials=default_creds)
        sa_name = f"projects/-/serviceAccounts/{sa_email}"
        sign_jwt_request = iam_credentials_v1.SignJwtRequest(name=sa_name, payload=json.dumps(payload))
        sign_jwt_response = iam_client.sign_jwt(request=sign_jwt_request)
        signed_jwt = sign_jwt_response.signed_jwt
    except Exception as e:
        print(f"Failed to sign JWT: {e}")
        raise

    try:
        response = requests.post(
            token_uri,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": signed_jwt,
            },
        )
        response.raise_for_status()
        token_data = response.json()
        return credentials.Credentials(token=token_data["access_token"])
    except requests.exceptions.HTTPError as e:
        print(f"Failed to exchange access token: {e.response.text}")
        raise

def create_source(notebook_id: str, file_content: bytes, file_name: str):
    """Creates a new source by uploading a file."""
    creds = get_access_token()
    if not creds:
        print("Could not get NotebookLM token. Aborting create_source.")
        return None

    # Robust MIME type detection
    mime_map = {
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.mp4': 'video/mp4'
    }
    file_ext = os.path.splitext(file_name)[1].lower()
    mime_type = mime_map.get(file_ext)

    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_name)
    
    if not mime_type:
        mime_type = "application/octet-stream"

    # Special URL for file uploads
    upload_url = f"https://global-discoveryengine.googleapis.com/upload/v1alpha/projects/{config.PROJECT_NUMBER}/locations/{config.NOTEBOOK_LOCATION}/notebooks/{notebook_id}/sources:uploadFile"
    
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": mime_type,
        "X-Goog-Upload-File-Name": file_name, # Use the raw, un-encoded filename
        "X-Goog-Upload-Protocol": "raw"
    }

    print(f"DEBUG: Uploading file to create source. URL: {upload_url}")
    response = requests.post(upload_url, headers=headers, data=file_content)

    if response.status_code == 200:
        upload_response = response.json()
        source_id = upload_response.get('sourceId', {}).get('id')
        if not source_id:
            print("--- ERROR: 'sourceId' not found in upload response ---")
            return None
        
        # Construct a synthetic source object for the polling logic to use
        new_source = {
            "name": f"projects/{config.PROJECT_NUMBER}/locations/{config.NOTEBOOK_LOCATION}/notebooks/{notebook_id}/sources/{source_id}",
            "displayName": file_name # Use the original, non-encoded filename
        }
        print(f"Successfully created source '{file_name}' with ID: {new_source.get('name')}")
        return new_source
    else:
        print("--- ERROR: Failed to create source ---")
        print(f"URL: {upload_url}")
        print(f"STATUS_CODE: {response.status_code}")
        print(f"RESPONSE_TEXT: {response.text}")
        print("--- END ERROR ---")
        return None

def get_source(notebook_id: str, source_id: str):
    """Retrieves a specific source from a notebook."""
    creds = get_access_token()
    if not creds:
        print("Could not get NotebookLM token. Aborting get_source.")
        return None

    url = f"{API_BASE_URL}/projects/{config.PROJECT_NUMBER}/locations/{config.NOTEBOOK_LOCATION}/notebooks/{notebook_id}/sources/{source_id}"
    headers = {"Authorization": f"Bearer {creds.token}"}

    print(f"DEBUG: Getting source with URL: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("--- ERROR: Failed to get source ---")
        print(f"URL: {url}")
        print(f"STATUS_CODE: {response.status_code}")
        print(f"RESPONSE_TEXT: {response.text}")
        print("--- END ERROR ---")
        return None

def delete_source(notebook_id: str, source_name: str):
    """Deletes a source from a notebook using the batchDelete method."""
    creds = get_access_token()
    if not creds:
        print("Could not get NotebookLM token. Aborting delete_source.")
        return False

    url = f"{API_BASE_URL}/projects/{config.PROJECT_NUMBER}/locations/{config.NOTEBOOK_LOCATION}/notebooks/{notebook_id}/sources:batchDelete"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    data = {"names": [source_name]}

    print(f"DEBUG: Deleting source with URL: {url}")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Successfully deleted source '{source_name}'")
        return True
    else:
        print("--- ERROR: Failed to delete source ---")
        print(f"URL: {url}")
        print(f"STATUS_CODE: {response.status_code}")
        print(f"RESPONSE_TEXT: {response.text}")
        print("--- END ERROR ---")
        return False
