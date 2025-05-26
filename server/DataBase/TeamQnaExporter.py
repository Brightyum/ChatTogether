import json
import os
from datetime import datetime
from DataBase.db import Db


class TeamQnaExporter:
    def __init__(self, user_id, team_id):
        self.json_path = f"json/team_qna_{team_id}.json"
        self.db = Db().getDb()
        self.qna_json = self._load_json()
        self.user_id = user_id
        self.team_id = team_id

    def _load_json(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_json(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.qna_json, f, ensure_ascii=False, indent=4)

    def export_to_json(self):
        try:
            with self.db.cursor() as cursor:
                sql = """
                    SELECT message_id, Client_ID, Team_ID, conversation_id, Team_Asw, Team_Rsp, created_at
                    FROM TeamQna_Table
                    WHERE Client_ID = %s AND Team_ID = %s
                """
                cursor.execute(sql, (self.user_id, self.team_id))
                results = cursor.fetchall()

                added_count = 0
                skipped_count = 0

                for row in results:
                    (
                        message_id,
                        client_id,
                        team_id,
                        conversation_id,
                        user_question,
                        ai_response,
                        created_at,
                    ) = row
                    message_id_str = str(message_id)

                    # 중복 체크
                    if message_id_str in self.qna_json:
                        skipped_count += 1
                        continue

                    # 새로운 데이터만 추가
                    self.qna_json[message_id_str] = {
                        "질문자ID": client_id,
                        "팀ID": team_id,
                        "대화주제": conversation_id,
                        "질문": user_question,
                        "날짜": created_at.strftime("%Y-%m-%d"),
                        "응답": ai_response,
                    }
                    added_count += 1

                self._save_json()
                print(
                    f"[INFO] QnA JSON 저장 완료 (추가: {added_count}개, 중복 제외: {skipped_count}개)"
                )

        except Exception as e:
            print("DB 조회 또는 JSON 저장 중 오류:", e)
        finally:
            try:
                self.db.close()
            except:
                pass
