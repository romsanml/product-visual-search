from api.config import settings
from api.services.embeddings import ImageEmbedder
from api.services.vector_store import FaissStore
from api.services.storage import Storage

_embedder = ImageEmbedder(device=settings.device)
_vdb = FaissStore(dim=_embedder.dim, path=settings.faiss_index_path)
_storage = Storage(root_dir=settings.storage_root)

def get_embedder():
    return _embedder

def get_vdb():
    return _vdb

def get_storage():
    return _storage
