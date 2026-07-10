import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

class EmbeddingService:
    """
    Embedding service for generating text representations and calculating
    semantic similarity between artifacts.
    
    Supports:
    1. Local Hugging Face SentenceTransformer ('all-MiniLM-L6-v2').
    2. Fallback to local TF-IDF (scikit-learn) if Hugging Face is offline or blocked.
    """

    def __init__(self):
        import os
        self.model = None
        self.use_fallback = False

        if os.getenv("FORCE_TFIDF") == "1":
            print("EmbeddingService: FORCE_TFIDF set. Using local TF-IDF Vectorizer.")
            self.use_fallback = True
            return

        print("EmbeddingService: Attempting to load SentenceTransformer('all-MiniLM-L6-v2')...")
        try:
            from sentence_transformers import SentenceTransformer
            # Attempt to initialize (might trigger download if not cached)
            # Set a low timeout or catch exceptions if download hangs
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("EmbeddingService: SentenceTransformer loaded successfully.")
        except Exception as e:
            print(f"EmbeddingService: SentenceTransformer load/download failed: {e}.")
            print("EmbeddingService: Falling back to local TF-IDF Vectorizer (scikit-learn).")
            self.use_fallback = True

    def calculate_similarities(
        self,
        texts_a: List[str],
        texts_b: List[str],
    ) -> np.ndarray:
        """
        Compute similarity matrix of shape (len(texts_a), len(texts_b))
        containing cosine similarity values.
        """
        if not texts_a or not texts_b:
            return np.zeros((len(texts_a), len(texts_b)))

        if not self.use_fallback and self.model is not None:
            try:
                # Generate embeddings
                embeddings_a = self.model.encode(texts_a, convert_to_numpy=True)
                embeddings_b = self.model.encode(texts_b, convert_to_numpy=True)

                # Normalize to compute cosine similarity via dot product
                norm_a = embeddings_a / np.linalg.norm(embeddings_a, axis=1, keepdims=True)
                norm_b = embeddings_b / np.linalg.norm(embeddings_b, axis=1, keepdims=True)

                return np.dot(norm_a, norm_b.T)
            except Exception as e:
                print(f"EmbeddingService: SentenceTransformer encode failed: {e}. Trying TF-IDF fallback.")

        # Fallback to TF-IDF (local, offline, fast)
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # Combine corpora to fit vectorizer
            combined = texts_a + texts_b
            vectorizer = TfidfVectorizer(stop_words='english')
            vectorizer.fit(combined)

            vecs_a = vectorizer.transform(texts_a)
            vecs_b = vectorizer.transform(texts_b)

            return cosine_similarity(vecs_a, vecs_b)
        except Exception as e:
            print(f"EmbeddingService: Local TF-IDF calculation failed: {e}.")
            # Absolute fallback: Jaccard word-overlap matrix
            return self._jaccard_similarity_matrix(texts_a, texts_b)

    def _jaccard_similarity_matrix(
        self,
        texts_a: List[str],
        texts_b: List[str],
    ) -> np.ndarray:
        """
        Absolute offline fallback: Jaccard overlap coefficient matrix.
        """
        matrix = np.zeros((len(texts_a), len(texts_b)))
        words_a = [set(t.lower().split()) for t in texts_a]
        words_b = [set(t.lower().split()) for t in texts_b]

        for i, set_a in enumerate(words_a):
            for j, set_b in enumerate(words_b):
                union = set_a.union(set_b)
                if not union:
                    matrix[i, j] = 0.0
                else:
                    matrix[i, j] = len(set_a.intersection(set_b)) / len(union)
        return matrix
