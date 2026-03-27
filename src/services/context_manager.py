from .embedding import EmbeddingService
from ..db.chromadb_client import VectorDB
from ...api.connection_manager import ConnectionManager
class ContextManager:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_db = VectorDB()
        self.alert_service = ConnectionManager()