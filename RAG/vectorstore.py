from RAG.embedding import Embedding
from langchain_community.vectorstores import FAISS
import os
import json


class VectorStore:
    def __init__(self):
        self.embedding = Embedding()
        self.VECTORSTORE_PATH = "faiss_index"

    # 벡터 스토어를 읽어 들이는 기능
    def load_vectorstore(self, team_id=None):
        # 벡터스토어 경로 설정
        path = (
            os.path.join(self.VECTORSTORE_PATH, str(team_id))
            if team_id
            else self.VECTORSTORE_PATH
        )
        # 벡터스토어 필수 파일
        index_file = os.path.join(path, "index.faiss")
        pkl_file = os.path.join(path, "index.pkl")

        # 벡터스토어 필수 파일이 없을시 문제 발생 확인 기능
        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            raise FileNotFoundError(f"VectorStore 없음: {index_file}, {pkl_file}")

        # 기본 벡터스토어 저장
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

    # 벡터스토어에 문서 대입
    def embed_documents(self, docs, team_id):
        # 문서가 없을 경우 반환
        if not docs:
            print(f"[WARN] 임베딩할 문서가 없습니다. (team_id: {team_id})")
            return
        try:
            # 기존의 벡터스토어를 읽어들임
            vectorstore = self.load_vectorstore(team_id)
        except FileNotFoundError:
            print(
                f"[WARN] 기존 VectorStore 없음, 새로 생성합니다. (team_id: {team_id})"
            )
            # 벡터스토어가 없으면 새로 생성
            vectorstore = FAISS.from_documents(
                docs, embedding=self.embedding.get_embedding_model()
            )
            # 새로 생성된 벡터스토어 저장
            self.save_vectorstore(vectorstore, team_id)

            # 저장 후 메타데이터 확인
            for doc_id, doc in vectorstore.docstore._dict.items():
                print(f"[DEBUG][NEW STORE] Doc ID: {doc_id}")
                print(f"[DEBUG][NEW STORE] Content: {doc.page_content}")
                print(f"[DEBUG][NEW STORE] Metadata: {doc.metadata}")
            return

        # 기존에 벡터스토어가 있을 경우 같은 문서를 대입하는 것을 방지하기위해 해시함수를 통한 검증
        hash_set = self.embedding.get_hash_registry()
        print(f"[DEBUG] hash_set 크기: {len(hash_set)}")

        new_docs, new_hashes = [], set()
        for doc in docs:
            # 문서 내용을 기반으로 해시 생성
            chunk_hash = self.embedding.generate_chunk_hash(doc.page_content)
            print(f"[DEBUG] 문서 해시: {chunk_hash}")

            # 새로운 문서에 대한 해시값이 기존 해시값에 없는 경우 새 문서이므로 추가대상 포함
            if chunk_hash not in hash_set:
                new_docs.append(doc)
                new_hashes.add(chunk_hash)

        # 새로운 문서가 있을 경우 동작
        if new_docs:
            # 벡터스토어에 새로운 문서를 추가
            vectorstore.add_documents(new_docs)
            # 업데이트된 벡터스토어를 저장
            self.save_vectorstore(vectorstore, team_id)

            for doc_id, doc in vectorstore.docstore._dict.items():
                print(f"[DEBUG][AFTER ADD] Doc ID: {doc_id}")
                print(f"[DEBUG][AFTER ADD] Content: {doc.page_content}")
                print(f"[DEBUG][AFTER ADD] Metadata: {doc.metadata}")

            # 새로 추가된 해시값을 저장
            hash_set.update(new_hashes)
            self.embedding.save_hash_registry(hash_set)
            print(f"[INFO] {len(new_docs)}개의 문서 추가 완료")
        else:
            print("[INFO] 추가할 새 문서 없음")
