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
                documents=[], 
                embedding=self.embedding.get_embedding_model()
            )
            empty_vectorstore.save_local(self.VECTORSTORE_PATH)
        
    def set_vectorstore(self):
        existing_hash = self.embedding.get_hash_registry()
        split_docs = self.split.get_recursive_splitter()

        new_docs = []
        new_hashes = set()

        for doc in split_docs:
            doc_hash = self.embedding.generate_chunk_hash(doc.page_content)
            if doc_hash not in existing_hash:
                new_docs.append(doc)
                new_hashes.add(doc_hash)
        
        if not new_docs:
            print("추가된 새로운 청크는 없습니다.")
            return
        
        
        vectorstore = FAISS.load_local(
            folder_path=self.VECTORSTORE_PATH, 
            embeddings=self.embedding.get_embedding_model()
        )
        vectorstore.add_documents(new_docs)
        vectorstore.save_local(self.VECTORSTORE_PATH)
        
        existing_hash.update(new_hashes)
        self.embedding.save_hash_registry(self.embedding.get_path, existing_hash)
        
        print(f"{len(new_docs)}개의 새로운 청크가 벡터스토어에 추가 저장되었습니다.")
