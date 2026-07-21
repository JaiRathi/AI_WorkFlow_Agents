import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import config


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(
            config.embedding.model_name,
            device=config.embedding.device,
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=config.embedding.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

    def embed_single(self, text: str) -> np.ndarray:
        return self.model.encode(
            [text],
            normalize_embeddings=True,
        )[0]

    def embed_batch(self, docs: list[dict]) -> list[dict]:
        texts = [d.get("text", "") for d in docs]
        vectors = self.embed(texts)
        for i, doc in enumerate(docs):
            doc["vector"] = vectors[i].tolist()
        return docs
