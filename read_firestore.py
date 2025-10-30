from google.cloud import firestore

def read_collection():
    db = firestore.Client()
    collection_ref = db.collection("notebooklm_sources")
    docs = collection_ref.stream()
    doc_count = 0
    print("--- Documents in Firestore collection 'notebooklm_sources' ---")
    for doc in docs:
        print(f"Document ID: {doc.id}")
        print(f"Data: {doc.to_dict()}")
        print("---")
        doc_count += 1
    print(f"Found {doc_count} documents.")

if __name__ == "__main__":
    read_collection()
