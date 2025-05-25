from langchain_text_splitters import RecursiveCharacterTextSplitter
from RAG.load import Load

class Split:
    def __init__(self, chunk_size=250, chunk_overlap=50):
        self.load = Load()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def get_recursive_splitter(self) -> list:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

        split_docs = splitter.split_documents(self.load.get_json_to_documents())

        return split_docs
    
def main():
    s = Split()
    s.recursive_splitter()

if __name__ == "__main__":
    main()