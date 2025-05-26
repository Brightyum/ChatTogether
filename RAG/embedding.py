import json
import os
import hashlib
from langchain_openai import OpenAIEmbeddings


class Embedding:
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings()
        self.HASH_REGISTRY_PATH = "json/hash_registry.json"

    def get_embedding_model(self):
        return self.embedding_model

    def get_hash_registry(self) -> set:
        if not os.path.exists(self.HASH_REGISTRY_PATH):
            return set()
        with open(self.HASH_REGISTRY_PATH, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return set(data) if isinstance(data, list) else set()
            except json.JSONDecodeError:
                return set()

    def save_hash_registry(self, hash_set: set):
        with open(self.HASH_REGISTRY_PATH, "w", encoding="utf-8") as file:
            json.dump(list(hash_set), file, ensure_ascii=False, indent=2)

    def generate_chunk_hash(self, text):
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
