from api.config import settings
from api.services.embeddings import ImageEmbedder
from api.services.vector_store import FaissStore
from api.services.storage import Storage
from api.services.gdino_search import GroundingDINOSearcher

_embedder = ImageEmbedder(device=settings.device)
_vdb = FaissStore(dim=_embedder.dim, path=settings.faiss_index_path)
_storage = Storage(root_dir=settings.storage_root)
_searcher = GroundingDINOSearcher(device=settings.device)

def get_embedder():
    return _embedder

def get_vdb():
    return _vdb

def get_storage():
    return _storage

def get_searcher():
    return _searcher