# Requirements: pip install sentence-transformers faiss-cpu

import faiss
import pickle
from sentence_transformers import SentenceTransformer

class ContextCreator():
    def __init__(self):
        self._index = faiss.read_index("/home/wym92549/mw/docs_index.faiss")
        with open("/home/wym92549/mw/docs_paragraphs.pkl", "rb") as f:
            self._docs = pickle.load(f)
        self._embed_model = SentenceTransformer('all-MiniLM-L6-v2')

    def retrieve(self, user_prompt, k=5):
        q_emb = self._embed_model.encode([user_prompt])
        D, I = self._index.search(q_emb, k)  # Top-k nearest neighbors
        context = ", ".join([self._docs[i] for i in I[0]])
        return "{" + f"dynamic_context: {context}" + "}"

