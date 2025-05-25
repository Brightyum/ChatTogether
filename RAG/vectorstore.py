from embedding import Embedding
from split import Split
from langchain_community.vectorstores import FAISS
import os


class VectorStore:
    def __init__(self):
        self.embedding = Embedding()
        self.split = Split()
        self.VECTORSTORE_PATH = "faiss_index"

        if not os.path.exists(self.VECTORSTORE_PATH):
            empty_vectorstore = FAISS.from_documents(
                documents=[], embedding=self.embedding.get_embedding_model()
            )
            empty_vectorstore.save_local(self.VECTORSTORE_PATH)

    def is_semantically_duplicate(self, vectorstore, doc, threshold=0.95):
        embedding_model = self.embedding.get_embedding_model()
        query_vector = embedding_model.embed_query(doc.page_content)
        similar_docs = vectorstore.similarity_search_by_vector(query_vector, k=1)

        if similar_docs:
            return True
        
        return False
    
    # team_id를 받아 team_id의 문서를 할당해주는 코드로 개선선
    def load_vectorstore(self, team_id=None):
        return FAISS.load_local(
            folder_path=self.VECTORSTORE_PATH,
            embeddings=self.embedding.get_embedding_model()
        )

    def set_vectorstore(self):
        existing_hash = self.embedding.get_hash_registry()
        split_docs = self.split.get_recursive_splitter()

        vectorstore = FAISS.load_local(
            folder_path=self.VECTORSTORE_PATH,
            embeddings=self.embedding.get_embedding_model(),
        )

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
        vectorstore.save_local(self.VECTORSTORE_PATH)

        existing_hash.update(new_hashes)
        self.embedding.save_hash_registry(self.embedding.get_path, existing_hash)

        print(f"{len(new_docs)}개의 새로운 청크가 벡터스토어에 추가 저장되었습니다.")
