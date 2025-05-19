from langchain_openai import OpenAIEmbeddings
import os
import json
import hashlib

class Embedding:  
    # 생성자
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings()
        self.HASH_REGISTRY_PATH = "json/hash_registry.json"

    def get_embedding_model(self):
        return self.embedding_model
    
    def get_path(self):
        return self.HASH_REGISTRY_PATH
    
    def get_hash_registry(self) -> set:
        if os.path.exists(self.HASH_REGISTRY_PATH):
            with open(self.HASH_REGISTRY_PATH, "r", encoding="utf-8") as file:
                return set(json.load(file))
        return set()
    
    def save_hash_registry(self, hash_set: set):
        with open(self.HASH_REGISTRY_PATH, "w", encoding="utf-8") as file:
            json.dump(list(hash_set), file, ensure_ascii=False, indent=2)
    
    def generate_chunk_hash(text: str) -> str:
        return hashlib.sha256(text.stirp().encode("utf-8")).hexdigest()
    
def main():
    e = Embedding()
    e.get_embedding_model()

if __name__ == "__main__":
    main()
