import json
import os
from langchain.docstore.document import Document
from datetime import datetime


class Load:
    def __init__(self, team_id):
        from dotenv import load_dotenv
        import os

        load_dotenv()
        os.getenv("OPENAI_API_KEY")

        self.JSON_PATH = f"json/team_qna_{team_id}.json"
        self.ensure_json_file_exists()

    def ensure_json_file_exists(self):
        today = datetime.now().strftime("%Y-%m-%d")
        team_id = self.JSON_PATH.split("_")[-1].split(".")[0]  # 파일명에서 team_id 추출

        basic_data = {
            "1": {
                "질문자ID": "system",
                "팀ID": team_id,
                "대화주제": "팀 협업",
                "질문": "팀 협업 시스템이란 무엇인가요?",
                "날짜": today,
                "응답": "팀 협업 시스템은 여러 명이 함께 정보를 공유하고, 작업을 분담하여 효율적으로 프로젝트를 수행하는 시스템입니다.",
            }
        }
        """파일이 없으면 빈 JSON 파일 생성"""
        if not os.path.exists(self.JSON_PATH):
            with open(self.JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(basic_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] {self.JSON_PATH} 생성 완료 (JSON 파일)")

    def load_json_file(self) -> dict:
        try:
            with open(self.JSON_PATH, "r", encoding="utf-8") as file:
                json_data = json.load(file)
            return json_data
        except Exception as e:
            print(f"Json파일 로드중 에러 발생: {e}")
            return {}

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
