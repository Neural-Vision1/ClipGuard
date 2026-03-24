import chromadb
from chromadb.config import Settings
from ..utils.logger import logging
class VectorDB:
    def __init__(self, persist_directory="./chromadb_storage"):
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(allow_reset=True)
        )
        self.collection_name = "video_embeddings"
        self.collections = self.client.get_or_create_collection(self.collection_name)

    def add_embeddings(self, embeddings, metadata_list):
        try:
            logging.debug(f"Embedding inside VectorDB {len(embeddings)}")
            ids = [f"id_{meta['video_id']}_{meta['timestamp']}" for meta in metadata_list]
            self.collections.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadata_list
            )
        except Exception as e:
            logging.debug(f"VectorDB : {e}")
    def search(self, embedding, top_k=5):
        try:
            result = self.collections.query(query_embeddings=[embedding], n_results=top_k)
            return result
        except Exception as e:
            return []

    def format_results(self, raw_results):
        formatted = []

        matches = raw_results.get("metadatas", [[]])[0]
        scores = raw_results.get("distances", [[]])[0]

        for meta, score in zip(matches, scores):
            formatted.append({
                "video_id": meta.get("video_id"),
                "timestamp": meta.get("timestamp"),
                "score": 1 - score
            })
        return formatted

    def clear_collection(self):
        self.client.delete_collection(self.collection_name)
        self.collections = self.client.create_collection(self.collection_name)


