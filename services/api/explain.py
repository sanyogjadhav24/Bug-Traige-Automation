# Lightweight placeholder. You can enable SHAP when data volume is sufficient.
# For now, we return most similar historical examples by cosine similarity.

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def similar_cases(emb: np.ndarray, emb_matrix: np.ndarray, ids: list[str], top_k:int=5):
    if emb_matrix is None or len(ids) == 0:
        return []
    sims = cosine_similarity(emb.reshape(1,-1), emb_matrix)[0]
    idx = np.argsort(-sims)[:top_k]
    return [{"id": ids[i], "similarity": float(sims[i])} for i in idx]
