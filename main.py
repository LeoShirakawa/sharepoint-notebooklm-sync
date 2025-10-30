import os
import time
from flask import Flask, request
import notebooklm_client
import sharepoint_client
import config
import firestore_client
from datetime import datetime, timezone

import google.auth

app = Flask(__name__)

# Log google-auth version at startup
print(f"google-auth version: {google.auth.__version__}")
print(f"SharePoint Site ID: {config.SHAREPOINT_SITE_ID}")
print(f"SharePoint Folder ID: {config.SHAREPOINT_FOLDER_ID}")

@app.route("/")
def hello_world():
    """Health check endpoint."""
    return "Service is running.", 200

@app.route("/sync", methods=['POST'])
def sync_notebook():
    """Main endpoint to trigger the synchronization process."""
    print("Sync process started.")

    # 1. Fetch current state from SharePoint and Firestore
    try:
        sp_files = sharepoint_client.list_files()
        synced_sources = firestore_client.get_all_sources()
    except Exception as e:
        print(f"Error fetching initial state: {e}")
        return "Failed to fetch initial state from SharePoint or Firestore.", 500

    if sp_files is None or synced_sources is None:
        return "Failed to get file/source lists. Check logs for details.", 500

    # 2. Prepare for comparison
    sp_file_map = {f['name']: f for f in sp_files}
    synced_source_map = {s['displayName']: s for s in synced_sources}

    # 3. Determine differences
    files_to_upload = []
    sources_to_delete = []

    # Find new files to upload
    for name, sp_file in sp_file_map.items():
        if name not in synced_source_map:
            print(f"Found new file to upload: {name}")
            files_to_upload.append(sp_file)

    # Find sources to delete (files in Firestore but not SharePoint)
    for name, synced_source in synced_source_map.items():
        if name not in sp_file_map:
            print(f"Found source to delete: {name}")
            sources_to_delete.append(synced_source)

    # 4. Execute changes
    deleted_count = 0
    for source in sources_to_delete:
        source_name = source['name'] # Full resource name from Firestore record
        display_name = source['displayName']
        print(f"Deleting source '{display_name}' from NotebookLM and Firestore...")
        if notebooklm_client.delete_source(config.NOTEBOOK_ID, source_name):
            firestore_client.delete_source(display_name)
            deleted_count += 1

    created_count = 0
    for sp_file in files_to_upload:
        file_id = sp_file['id']
        file_name = sp_file['name']
        print(f"Downloading content for {file_name}...")
        content = sharepoint_client.download_file_content(file_id)
        
        if not content:
            print(f"Skipping {file_name} due to download failure.")
            continue

        print(f"Uploading source for {file_name} to NotebookLM...")
        initial_source_response = notebooklm_client.create_source(config.NOTEBOOK_ID, content, file_name)

        if not initial_source_response or 'name' not in initial_source_response:
            print(f"Failed to get initial source response for {file_name}.")
            continue

        # --- POLLING LOGIC ---
        source_name = initial_source_response['name']
        source_id = source_name.split('/')[-1]
        
        print(f"Source upload accepted for {file_name}. Polling for processing status (ID: {source_id})...")
        
        is_processed = False
        for i in range(10): # Poll for 1 minute (10 * 6 seconds)
            print(f"Polling attempt {i+1}/10 for source {source_id}...")
            source_details = notebooklm_client.get_source(config.NOTEBOOK_ID, source_id)
            
            if source_details:
                status = source_details.get('settings', {}).get('status', 'UNKNOWN')
                print(f"Current status for source {source_id}: {status}")

                if status == 'SOURCE_STATUS_COMPLETE':
                    print(f"Source processing complete for {file_name}.")
                    # Override the displayName with the original filename to ensure consistency with Firestore.
                    source_details['displayName'] = file_name
                    firestore_client.add_source(source_details)
                    created_count += 1
                    is_processed = True
                    break
                elif status == 'SOURCE_STATUS_FAILED':
                    print(f"--- ERROR: Source processing failed for {file_name} ---")
                    print(f"Details: {source_details.get('settings')}")
                    is_processed = True
                    break
            else:
                print(f"Source {source_id} not yet found. Retrying...")

            time.sleep(6)

        if not is_processed:
            print(f"--- ERROR: Polling timed out for source {file_name} (ID: {source_id}) ---")

    summary = f"Sync process finished. Created: {created_count}, Deleted: {deleted_count}."
    print(summary)
    return summary, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))