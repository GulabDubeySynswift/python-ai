import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
print(client.list_collections())
collection = client.get_or_create_collection("my_collection")
collection.add(
    documents=["This is document1", "This is document2"],
    metadatas=[{"source": "notion"}, {"source": "google-docs"}],
    ids=["doc1", "doc2"],
)
print(collection.count())
results = collection.query(
    query_texts=["This is a query document"],
    n_results=2,
)

print(results)

from sentence_transformers import SentenceTransformer
print("Adding new documents...")
model = SentenceTransformer("all-MiniLM-L6-v2")
new_embeddings = model.encode(["This is document3", "This is document4"]).tolist()
new_collection = client.get_or_create_collection("new_collection")
new_collection.add(
    embeddings=new_embeddings,
    ids=["doc3", "doc4"],
    metadatas=[{"source": "notion"}, {"source": "google-docs"}],
)
print("New documents added...") 
print(new_collection.count())
print("Querying new documents...")
results = new_collection.query(
    query_texts=["This is document3"],
    n_results=2,
)
print("Query results...")
print(results)
print("Query results...")