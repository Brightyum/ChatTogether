import json
from langchain.docstore.document import Document


class Load:
    def __init__(self, team_id):
        from dotenv import load_dotenv
        import os

        load_dotenv()
        os.getenv("OPENAI_API_KEY")

        self.JSON_PATH = f"json/team_qna_{team_id}.json"

    def load_json_file(self) -> dict:
        with open(self.JSON_PATH, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        return json_data

    def get_json_to_documents(self) -> list[Document]:
        json_data = self.load_json_file()
        docs = []

        for key, qa_pair in json_data.items():
            question = qa_pair.get("질문")
            answer = qa_pair.get("응답")
            user_id = qa_pair.get("질문자ID")
            team_id = qa_pair.get("팀ID")
            topic = qa_pair.get("대화주제")
            date = qa_pair.get("날짜")

            if not (question and answer):
                continue

            doc = Document(
                page_content=question,  # 질문만 벡터화
                metadata={
                    "답변": answer,
                    "질문자ID": user_id,
                    "팀ID": team_id,
                    "대화주제": topic,
                    "날짜": date,
                },
            )
            docs.append(doc)

        print(f"[INFO] Loaded {len(docs)} documents from {self.JSON_PATH}")
        return docs


def main():
    l = Load()
    l.get_json_to_documents()


if __name__ == "__main__":
    main()
