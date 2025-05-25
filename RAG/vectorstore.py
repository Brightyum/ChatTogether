from RAG.embedding import Embedding
from RAG.split import Split
from langchain_community.vectorstores import FAISS
import os


class VectorStore:
    def __init__(self):
        self.embedding = Embedding()
        self.split = Split()
        self.VECTORSTORE_PATH = "faiss_index"

        # self.index_file = os.path.join(self.VECTORSTORE_PATH, "index.faiss")
        # self.pkl_file = os.path.join(self.VECTORSTORE_PATH, "index.pkl")
        # self.set_file()
        # if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        #     empty_vectorstore = FAISS.from_documents(
        #         documents=[], embedding=self.embedding.get_embedding_model()
        #     )
        #     empty_vectorstore.save_local(self.VECTORSTORE_PATH)

    def set_file(self, team_id=None):
        path = self.VECTORSTORE_PATH
        if team_id:
            path = os.path.join(path, str(team_id))

        index_file = os.path.join(path, "index.faiss")
        pkl_file = os.path.join(path, "index.pkl")

        if not os.path.exists(path):
            os.makedirs(path)

        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            print("[INFO] FAISS 인덱스 파일이 없어 초기화 진행...")

            # 최소한의 임베딩 벡터 크기 알아내기
            test_embedding_model = self.embedding.get_embedding_model()
            dummy_vector = test_embedding_model.embed_query("dummy")

            import faiss
            d = len(dummy_vector)
            index = faiss.IndexFlatL2(d)
            faiss.write_index(index, index_file)

            # 빈 메타파일 저장 (LangChain 요구사항에 따라)
            import pickle
            with open(pkl_file, "wb") as f:
                pickle.dump({"docstore": {}, "index_to_docstore_id": {}, "docstore_id_to_index": {}}, f)

            print("[INFO] 빈 FAISS 인덱스 및 메타파일 초기화 완료.")

    def is_semantically_duplicate(self, vectorstore, doc, threshold=0.95):
        embedding_model = self.embedding.get_embedding_model()
        query_vector = embedding_model.embed_query(doc.page_content)
        similar_docs = vectorstore.similarity_search_by_vector(query_vector, k=1)

        if similar_docs:
            return True
        
        return False
    
    # team_id를 받아 team_id의 문서를 할당해주는 코드로 개선선
    def load_vectorstore(self, team_id=None):
        path = self.VECTORSTORE_PATH
        if team_id:
            path = os.path.join(path, str(team_id))

        self.set_file(team_id)

        vectorstore = FAISS.load_local(
            folder_path=path,
            embeddings=self.embedding.get_embedding_model(),
            allow_dangerous_deserialization=True  # 보안 예외 허용
        )

        return vectorstore 

    def save_vectorstore(self, vectorstore, team_id=None):
        path = self.VECTORSTORE_PATH
        if team_id:
            path = os.path.join(path, f"{team_id}")

        if not os.path.exists(path):
            os.makedirs(path)
        
        vectorstore.save_local(path)
        print(f"[INFO] 팀 {team_id} 벡터스토어 저장 완료: {path}")

    def set_vectorstore(self, team_id):
        self.set_file(team_id)
        existing_hash = self.embedding.get_hash_registry()
        split_docs = self.split.get_recursive_splitter()

        # vectorstore = FAISS.load_local(
        #     folder_path=self.VECTORSTORE_PATH,
        #     embeddings=self.embedding.get_embedding_model(),
        # )
        vectorstore= self.load_vectorstore(team_id=team_id)

        new_docs = []
        new_hashes = set()

        for doc in split_docs:
            doc_hash = self.embedding.generate_chunk_hash(doc.page_content)

            if doc_hash not in existing_hash:
                continue

            if self.is_semantically_duplicate(vectorstore, doc):
                continue

            new_docs.append(doc)
            new_hashes.add(doc_hash)

        if not new_docs:
            print("추가된 새로운 청크는 없습니다.")
            return

        vectorstore.add_documents(new_docs)
        self.save_vectorstore(vectorstore, team_id=team_id)

        existing_hash.update(new_hashes)
        self.embedding.save_hash_registry(self.embedding.get_path, existing_hash)

        print(f"{len(new_docs)}개의 새로운 청크가 벡터스토어에 추가 저장되었습니다.")
