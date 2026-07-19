from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, OptimizersConfigDiff
from fastembed import SparseTextEmbedding

from config.settings import config


class QdrantManager:
    def __init__(self):
        self._client = None
        self._sparse_embedder = None
        self._collections_ok = False

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(
                url=config.qdrant.url,
                api_key=config.qdrant.api_key or None,
                prefer_grpc=config.qdrant.prefer_grpc,
            )
        return self._client

    @property
    def sparse_embedder(self):
        if self._sparse_embedder is None:
            self._sparse_embedder = SparseTextEmbedding(model_name="Qdrant/bm25")
        return self._sparse_embedder

    def ensure_collections(self) -> None:
        if self._collections_ok:
            return
        existing = {c.name for c in self.client.get_collections().collections}
        for name, collection_name in config.collections.items():
            if collection_name not in existing:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=config.embedding.dimension,
                        distance=Distance.COSINE,
                    ),
                    sparse_vectors_config={"bm25": SparseVectorParams()},
                    optimizers_config=OptimizersConfigDiff(
                        indexing_threshold=20000,
                    ),
                )
                print(f"[Qdrant] Created collection: {collection_name}")
        self._collections_ok = True

    def get_collection(self, source_type: str) -> str:
        return config.collections.get(source_type, f"{config.collection_prefix}_{source_type}")

    def upsert_points(self, collection_name: str, points: list[dict]) -> None:
        self.client.upsert(
            collection_name=collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
                for p in points
            ],
        )

    def delete_collection(self, collection_name: str) -> None:
        self.client.delete_collection(collection_name=collection_name)
        self._collections_ok = False

    def count_points(self, collection_name: str) -> int:
        info = self.client.get_collection(collection_name=collection_name)
        return info.points_count

    def search_dense(
        self, collection_name: str, query_vector: list[float], top_k: int = 5, filter_condition: Optional[dict] = None
    ) -> list[dict]:
        query_filter = qdrant_models.Filter(**filter_condition) if filter_condition else None
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]

    def search_sparse(
        self, collection_name: str, query_text: str, top_k: int = 5, filter_condition: Optional[dict] = None
    ) -> list[dict]:
        sparse_vector = list(self.sparse_embedder.query_embed(query_text))[0]
        query_filter = qdrant_models.Filter(**filter_condition) if filter_condition else None
        results = self.client.search(
            collection_name=collection_name,
            query_vector=qdrant_models.NamedVector(name="bm25", vector=sparse_vector.values.tolist()),
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]

    def hybrid_search(
        self,
        collection_name: str,
        query_text: str,
        query_vector: list[float],
        top_k: int = 5,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        filter_condition: Optional[dict] = None,
    ) -> list[dict]:
        dense_results = self.search_dense(collection_name, query_vector, top_k=top_k, filter_condition=filter_condition)
        return dense_results


qdrant_manager = QdrantManager()
