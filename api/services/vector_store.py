import os
import numpy as np
import faiss

class FaissStore:
    def __init__(self, dim: int, path: str):
        self.dim = dim
        self.path = path
        self.index = self._load_or_create()

    def _load_or_create(self):
        if os.path.isfile(self.path):
            idx = faiss.read_index(self.path)
            if not isinstance(idx, (faiss.IndexIDMap, faiss.IndexIDMap2)):
                idx = faiss.IndexIDMap2(idx)
            return idx
        base = faiss.IndexFlatIP(self.dim)  # под косинус, т.к. вектора L2-нормированы
        return faiss.IndexIDMap2(base)

    def save(self):
        faiss.write_index(self.index, self.path)

    def upsert(self, vec: np.ndarray, id_: int):
        ids = np.array([id_], dtype=np.int64)
        self.index.remove_ids(ids)
        self.index.add_with_ids(vec.reshape(1, -1).astype("float32"), ids)

    def search(self, vec: np.ndarray, top_k: int = 10):
        if self.index.ntotal == 0:
            return [], []
        D, I = self.index.search(vec.reshape(1, -1).astype("float32"), top_k)
        return I[0].tolist(), D[0].tolist()
