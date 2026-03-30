import faiss
import numpy as np
from collections import deque
import uuid

class LiveMemoryIndex:
    def __init__(self,dim=512,max_size=120):
        self.dim = dim
        self.max_size = max_size
        self.index = faiss.IndexFlatIP(dim)
        self.embeddings = deque()
        self.ids = deque()
        self.frame = deque()
    def add_embeddings(self,vector:np.ndarray,frame_no):
        vector = vector.astype(np.float32)
        if len(self.embeddings) >= self.max_size:
            self._remove_oldest()
        embd_id = str(uuid.uuid4())
        self.index.add(vector.reshape(1,-1))
        self.embeddings.append(vector)
        self.ids.append(embd_id)
        self.frame.append(frame_no)
    def _remove_oldest(self):
        self.embeddings.popleft()
        self.ids.popleft()
        self.frame.popleft()
        self.index.reset()
        if self.embeddings:
            self.index.add(np.array(self.embeddings))
    def search(self,vector:np.ndarray,top_k=3):
        vector = vector.astype(np.float32)
        scores, idxs = self.index.search(vector.reshape(1,-1),top_k)
        return scores[0],idxs[0]