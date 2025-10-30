from google.cloud import firestore

def clear_collection():
    db = firestore.Client()
    collection_ref = db.collection("notebooklm_sources")
    docs = collection_ref.stream()
    deleted_count = 0
    for doc in docs:
        print(f"Deleting doc {doc.id} => {doc.to_dict()}")
        doc.reference.delete()
        deleted_count += 1
    print(f"Deleted {deleted_count} documents from collection 'notebooklm_sources'.")

if __name__ == "__main__":
    clear_collection()
