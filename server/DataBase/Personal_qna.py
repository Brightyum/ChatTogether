import json
import os
from datetime import datetime
from DataBase.db import Db


class PersonalQnaExporter:

    def __init__(self, json_path="json/personal_qna.json"):
        self.json_path = json_path
        self.db = Db().getDb()
        self.qna_json = self._load_json()

    def _load_json(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_json(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.qna_json, f, ensure_ascii=False, indent=4)


    def save_to_db(self, client_id, user_question, ai_response, topic_summary="대화요약미정"):
        try:
            with self.db.cursor() as cursor:
                sql = """
                    INSERT INTO Personal_Table (Client_ID, conversation_id, Personal_Asw, Personal_Rsp)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (client_id, topic_summary, user_question, ai_response))
                self.db.commit()

                # 마지막 삽입된 메시지 ID 조회
                cursor.execute("SELECT LAST_INSERT_ID()")
                message_id = cursor.fetchone()[0]

                # 삽입된 날짜 정보도 가져오기
                cursor.execute("SELECT created_at FROM Personal_Table WHERE message_id = %s", (message_id,))
                created_at = cursor.fetchone()[0].strftime("%Y-%m-%d")

                # JSON으로 저장
                self.qna_json[str(message_id)] = {
                    "질문자ID": client_id,
                    "대화주제": topic_summary,
                    "질문": user_question,
                    "날짜": created_at,
                    "응답": ai_response
                }
                self._save_json()

                return True
        except Exception as e:
            print("DB 저장 또는 JSON 생성 오류:", e)
            self.db.rollback()
            return False
        finally:
            try:
                self.db.close()
            except:
                pass
