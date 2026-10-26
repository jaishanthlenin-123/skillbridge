import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

class SemanticVectorizer:
    """
    Manages Sentence Transformer dense vector embeddings with fallback.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._is_fallback = False
        self._cache = {}

    def _load_model(self):
        if self._model is not None or self._is_fallback:
            return
        try:
            from sentence_transformers import SentenceTransformer
            # Load model onto CPU
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using deterministic token vectorizer fallback.")
            self._is_fallback = True

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384))
        
        self._load_model()
        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings
            except Exception as e:
                logger.warning(f"Embedding generation error: {e}. Falling back.")

        # Fallback: simple character n-gram/token tf-idf vectorizer
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        try:
            tfidf = vectorizer.fit_transform(texts).toarray()
            # Normalize to unit vectors
            norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return tfidf / norms
        except Exception:
            return np.ones((len(texts), 1))

    def compute_similarity(self, queries: List[str], documents: List[str]) -> np.ndarray:
        """
        Computes pairwise cosine similarity matrix between queries and documents.
        Returns shape (len(queries), len(documents)) with values in [0.0, 1.0].
        """
        if not queries or not documents:
            return np.zeros((len(queries), len(documents)))

        q_vecs = self.encode(queries)
        d_vecs = self.encode(documents)

        # Cosine similarity for unit vectors is simple dot product
        sim_matrix = np.dot(q_vecs, d_vecs.T)
        # Clamp to [0, 1]
        return np.clip(sim_matrix, 0.0, 1.0)

# Global singleton
vectorizer = SemanticVectorizer()
