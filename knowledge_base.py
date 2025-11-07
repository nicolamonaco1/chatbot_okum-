# knowledge_base.py
import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_FILE = "index.faiss"
META_FILE = "index_meta.json"
DATA_FILES = [
    "faq_servizio_clienti.txt",
    "consigli_profumeria.txt",
    "guida_olfattiva.txt"
]

class KnowledgeBase:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.texts = []
        self.index = None

    def load_data(self):
        """Legge tutti i file txt e prepara il corpus"""
        corpus = []
        for f in DATA_FILES:
            if not os.path.exists(f):
                continue
            with open(f, "r", encoding="utf-8") as fp:
                text = fp.read()
            corpus.extend([p.strip() for p in text.split("\n\n") if p.strip()])
        self.texts = corpus
        print(f"[KnowledgeBase] Caricati {len(corpus)} paragrafi totali.")

    def build_index(self):
        """Crea l'indice FAISS e salva i metadati"""
        if not self.texts:
            self.load_data()

        embeddings = self.model.encode(self.texts, show_progress_bar=True, convert_to_numpy=True)
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        faiss.write_index(index, INDEX_FILE)
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump({"texts": self.texts}, f, ensure_ascii=False, indent=2)
        print("[KnowledgeBase] Index creato e salvato.")

    def load_index(self):
        """Carica index + metadati"""
        if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
            print("[KnowledgeBase] Nessun index trovato, lo creo ora...")
            self.build_index()
        self.index = faiss.read_index(INDEX_FILE)
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.texts = meta["texts"]
        print(f"[KnowledgeBase] Index caricato con {len(self.texts)} paragrafi.")

    def search(self, query, top_k=3):
        """Ritorna i paragrafi più simili semanticamente"""
        if self.index is None:
            self.load_index()
        query_emb = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_emb)
        D, I = self.index.search(query_emb, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            results.append({
                "score": float(score),
                "text": self.texts[idx]
            })
        return results

