import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
KB_PATH = BASE_DIR / "knowledge_base.json"


class LocalRAG:
    def __init__(self):
        self.documents = []
        self.vectorizer = None
        self.matrix = None

        try:
            with open(KB_PATH, "r", encoding="utf-8-sig") as f:
                documents = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        if not isinstance(documents, list):
            return

        self.documents = [item for item in documents if isinstance(item, dict)]

        self.texts = [
            " ".join([
                item.get("condition", ""),
                " ".join(item.get("keywords", [])),
                item.get("summary", ""),
                item.get("self_care", ""),
                item.get("seek_care", ""),
                " ".join(item.get("red_flags", [])),
            ])
            for item in self.documents
        ]

        if not self.texts or not any(text.strip() for text in self.texts):
            return

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

        try:
            self.matrix = self.vectorizer.fit_transform(self.texts)
        except ValueError:
            self.vectorizer = None

    def search(self, query: str, top_k: int = 3):
        query = (query or "").strip()

        if not query or self.vectorizer is None or self.matrix is None:
            return []

        try:
            top_k = max(int(top_k), 0)
        except (TypeError, ValueError):
            return []

        if top_k == 0:
            return []

        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]

        ranked_indices = scores.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indices:
            score = float(scores[index])

            if score <= 0:
                continue

            item = dict(self.documents[index])
            item["score"] = round(score, 4)
            results.append(item)

        return results


rag = LocalRAG()


def retrieve_knowledge(query: str, top_k: int = 3):
    return rag.search(query, top_k=top_k)

