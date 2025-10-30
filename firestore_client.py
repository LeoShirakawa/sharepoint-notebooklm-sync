from google.cloud import firestore
import config

# Initialize Firestore client
db = firestore.Client()
COLLECTION_NAME = "notebooklm_sources"

def get_all_sources():
    """Fetches all source documents from the Firestore collection."""
    print("Fetching synced sources from Firestore...")
    sources = []
    docs = db.collection(COLLECTION_NAME).stream()
    for doc in docs:
        sources.append(doc.to_dict())
    print(f"Found {len(sources)} synced sources in Firestore.")
    return sources

def add_source(source_data):
    """
    Adds a new source document to Firestore.
    The document ID will be the source's display name.
    """
    # Normalize the data: the GET response uses 'title', but other parts expect 'displayName'
    if 'title' in source_data and 'displayName' not in source_data:
        source_data['displayName'] = source_data['title']

    if not source_data or 'displayName' not in source_data:
        print(f"ERROR: Invalid source data (missing displayName/title) provided to add_source. Data: {source_data}")
        return

    doc_id = source_data['displayName']
    print(f"Adding source record to Firestore: {doc_id}")
    db.collection(COLLECTION_NAME).document(doc_id).set(source_data)


def delete_source(source_display_name):
    """Deletes a source document from Firestore by its display name."""
    print(f"Deleting source record from Firestore: {source_display_name}")
    db.collection(COLLECTION_NAME).document(source_display_name).delete()