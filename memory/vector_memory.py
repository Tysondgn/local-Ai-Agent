# memory/vector_memory.py

from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

class VectorMemory:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # Light offline model
        self.embeddings = []
        self.metadata = []
        self.nn = None

    def add(self, text: str, meta: Dict):
        vec = self.model.encode(text)
        self.embeddings.append(vec)
        self.metadata.append(meta)
        self._rebuild_index()

    def add_memory(self, text: str, metadata: Dict = None):
        """Alias for add method to match expected interface"""
        if metadata is None:
            metadata = {}
        metadata["text"] = text  # Ensure text is stored in metadata
        self.add(text, metadata)

    def _rebuild_index(self):
        if self.embeddings:
            self.nn = NearestNeighbors(n_neighbors=3, metric="cosine")
            self.nn.fit(np.array(self.embeddings))

    def search(self, query: str, top_k=3) -> List[str]:
        if not self.embeddings:
            return []
        qvec = self.model.encode(query).reshape(1, -1)
        dists, indices = self.nn.kneighbors(qvec, n_neighbors=min(top_k, len(self.embeddings)))
        return [self.metadata[i]["text"] for i in indices[0]]

    def query(self, query: str, top_k=3) -> List[Dict]:
        """Alias for search method that returns metadata dicts"""
        if not self.embeddings:
            return []
        qvec = self.model.encode(query).reshape(1, -1)
        dists, indices = self.nn.kneighbors(qvec, n_neighbors=min(top_k, len(self.embeddings)))
        return [self.metadata[i] for i in indices[0]]
