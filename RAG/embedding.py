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
        path = self.get_path()
        if not os.path.exists(path):
            # 파일이 없으면 빈 set 반환
            return set()
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    print(f"[WARN] 해시 파일 형식 오류: {path}")
                    return set()
                return set(data)
            except json.JSONDecodeError:
                print(f"[WARN] 해시 파일이 비어있거나 잘못된 JSON 형식입니다: {path}")
                return set()
        # if os.path.exists(self.HASH_REGISTRY_PATH):
        #     with open(self.HASH_REGISTRY_PATH, "r", encoding="utf-8") as file:
        #         return set(json.load(file))
        # return set()

    def save_hash_registry(self, hash_set: set):
        with open(self.HASH_REGISTRY_PATH, "w", encoding="utf-8") as file:
            json.dump(list(hash_set), file, ensure_ascii=False, indent=2)

    def generate_chunk_hash(self, text):
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def main():
    e = Embedding()
    e.get_embedding_model()


if __name__ == "__main__":
    main()
