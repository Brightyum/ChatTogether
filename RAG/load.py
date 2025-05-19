import json
from langchain.docstore.document import Document

class Load:
    def __init__(self):
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        os.getenv("OPENAI_API_KEY")

        self.JSON_PATH = "json/qna.json"
        self.VECTORSTORE_PATH = ""
    
    def load_json_file(self) -> dict:
        with open(self.JSON_PATH, "r", encoding="utf-8") as file:
            json_data = json.load(file)
        
        return json_data

    def get_json_to_documents(self) -> list[Document]:
        json_data = self.load_json_file()
        docs = []

        for role_key, qa_pair in json_data.items():
            question = qa_pair.get("질문")
            answer = qa_pair.get("응답", {}).get("응답내용")
            model = qa_pair.get("응답", {}).get("모델")
            date = qa_pair.get("날짜")

            if not (question and answer):
                continue
            
            content = f"Q: {question}\nA: {answer}"
            metadata = {
                "role": role_key,
                "date": date,
                "model": model
            }

            docs.append(Document(page_content=content, metadata=metadata))
        print(docs)
        return docs
    
def main():
    l = Load()
    l.get_json_to_documents()

if __name__=="__main__":
    main()

