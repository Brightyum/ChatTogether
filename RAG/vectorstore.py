from RAG.embedding import Embedding
from langchain_community.vectorstores import FAISS
import os
import json


class VectorStore:
    def __init__(self):
        self.embedding = Embedding()
        self.VECTORSTORE_PATH = "faiss_index"

    def load_vectorstore(self, team_id=None):
        path = (
            os.path.join(self.VECTORSTORE_PATH, str(team_id))
            if team_id
            else self.VECTORSTORE_PATH
        )
        index_file = os.path.join(path, "index.faiss")
        pkl_file = os.path.join(path, "index.pkl")

        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            raise FileNotFoundError(f"VectorStore 없음: {index_file}, {pkl_file}")

        vectorstore = FAISS.load_local(
            folder_path=path,
            embeddings=self.embedding.get_embedding_model(),
            allow_dangerous_deserialization=True,
        )

        # ✅ 로드 후 메타데이터 확인
        for doc_id, doc in vectorstore.docstore._dict.items():
            print(f"[DEBUG][LOAD] Doc ID: {doc_id}")
            print(f"[DEBUG][LOAD] Content: {doc.page_content}")
            print(f"[DEBUG][LOAD] Metadata: {doc.metadata}")

        return vectorstore

    def save_vectorstore(self, vectorstore, team_id=None):
        path = (
            os.path.join(self.VECTORSTORE_PATH, str(team_id))
            if team_id
            else self.VECTORSTORE_PATH
        )
        os.makedirs(path, exist_ok=True)
        vectorstore.save_local(path)
        print(f"[INFO] VectorStore 저장 완료: {path}")

    def embed_documents(self, docs, team_id):
        try:
            vectorstore = self.load_vectorstore(team_id)
        except FileNotFoundError:
            print(
                f"[WARN] 기존 VectorStore 없음, 새로 생성합니다. (team_id: {team_id})"
            )
            vectorstore = FAISS.from_documents(
                docs, embedding=self.embedding.get_embedding_model()
            )
            self.save_vectorstore(vectorstore, team_id)
            # 저장 후 메타데이터 확인
            for doc_id, doc in vectorstore.docstore._dict.items():
                print(f"[DEBUG][NEW STORE] Doc ID: {doc_id}")
                print(f"[DEBUG][NEW STORE] Content: {doc.page_content}")
                print(f"[DEBUG][NEW STORE] Metadata: {doc.metadata}")
            return  # ✅ 새로 생성했으므로 여기서 끝

        hash_set = self.embedding.get_hash_registry()
        print(f"[DEBUG] hash_set 크기: {len(hash_set)}")

        new_docs, new_hashes = [], set()
        for doc in docs:
            chunk_hash = self.embedding.generate_chunk_hash(doc.page_content)
            print(f"[DEBUG] 문서 해시: {chunk_hash}")

            if chunk_hash not in hash_set:
                new_docs.append(doc)
                new_hashes.add(chunk_hash)

        if new_docs:
            vectorstore.add_documents(new_docs)
            self.save_vectorstore(vectorstore, team_id)

            for doc_id, doc in vectorstore.docstore._dict.items():
                print(f"[DEBUG][AFTER ADD] Doc ID: {doc_id}")
                print(f"[DEBUG][AFTER ADD] Content: {doc.page_content}")
                print(f"[DEBUG][AFTER ADD] Metadata: {doc.metadata}")

            hash_set.update(new_hashes)
            self.embedding.save_hash_registry(hash_set)
            print(f"[INFO] {len(new_docs)}개의 문서 추가 완료")
        else:
            print("[INFO] 추가할 새 문서 없음")
