from RAG.embedding import Embedding
from RAG.split import Split
from langchain_community.vectorstores import FAISS
import os


class VectorStore:
    def __init__(self):
        self.embedding = Embedding()
        self.split = Split()
        self.VECTORSTORE_PATH = "faiss_index"

    def is_semantically_duplicate(self, vectorstore, doc):
        if not vectorstore:
            print("[ERROR] vectorstore가 로드되지 않았습니다.")
            return False

        similar_docs = vectorstore.similarity_search(doc.page_content, k=1)
        return bool(similar_docs)

    def load_vectorstore(self, team_id=None):
        path = self.VECTORSTORE_PATH
        if team_id is not None:
            path = os.path.join(path, str(team_id))

        index_file = os.path.join(path, "index.faiss")
        pkl_file = os.path.join(path, "index.pkl")
        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            raise FileNotFoundError(
                f"[ERROR] FAISS 인덱스 파일이 존재하지 않습니다: {index_file}, {pkl_file}"
            )

        return FAISS.load_local(
            folder_path=path,
            embeddings=self.embedding.get_embedding_model(),
            allow_dangerous_deserialization=True,
        )

    def save_vectorstore(self, vectorstore, team_id=None):
        path = self.VECTORSTORE_PATH
        if team_id is not None:
            path = os.path.join(path, str(team_id))

        if not os.path.exists(path):
            os.makedirs(path)

        vectorstore.save_local(path)
        print(
            f"[INFO] 팀 {team_id if team_id is not None else '공용'} 벡터스토어 저장 완료: {path}"
        )

    def set_vectorstore(self, team_id):
        split_docs = self.split.get_recursive_splitter()
        embedding_model = self.embedding.get_embedding_model()

        try:
            vectorstore = self.load_vectorstore(team_id)
            print(f"[INFO] 기존 FAISS 벡터스토어 로드 완료 (team_id: {team_id})")
        except Exception as e:
            print(f"[WARN] 로드 실패, 새로 생성 (team_id: {team_id}): {e}")
            vectorstore = FAISS.from_documents(split_docs, embedding=embedding_model)
            self.save_vectorstore(vectorstore, team_id)

        existing_hash = self.embedding.get_hash_registry()
        new_docs = []
        new_hashes = set()

        for doc in split_docs:
            doc_hash = self.embedding.generate_chunk_hash(doc.page_content)
            if doc_hash not in existing_hash:
                new_docs.append(doc)
                new_hashes.add(doc_hash)

        if new_docs:
            vectorstore.add_documents(new_docs)
            self.save_vectorstore(vectorstore, team_id)
            existing_hash.update(new_hashes)
            self.embedding.save_hash_registry(self.embedding.get_path, existing_hash)
            print(f"[INFO] {len(new_docs)}개의 새로운 청크 추가 완료")
        else:
            print("[INFO] 추가할 새 문서 없음")
