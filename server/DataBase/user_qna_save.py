from .db import Db


class UserQnaSave:
    def __init__(self):
        self.db = Db().getDb()

    def save_team_chat_messages(self, user_id, team_id, question, answer, summary):
        try:
            with self.db.cursor() as cursor:
                sql = """
                    INSERT INTO TeamQna_Table (Team_ID, Client_ID, conversation_id, Team_Asw, Team_Rsp)
                    VALUES (%s, %s, %s, %s, %s)
                """

                cursor.execute(sql, (team_id, user_id, summary, question, answer))
            self.db.commit()
        except Exception as e:
            print("[팀 QnA 저장 오류]", e)
            self.db.rollback()

    def save_chat_messages(self, user_id, question, answer, summary):
        try:
            with self.db.cursor() as cursor:
                sql = """
                    INSERT INTO Personal_Table (Client_ID, conversation_id, Personal_Asw, Personal_Rsp)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, summary, question, answer))
            self.db.commit()
        except Exception as e:
            print(
                f"user_id: {user_id}\nquestion: {question}\nfinal_answer:{answer}\nsummary: {summary}"
            )
            print("[단일 QnA 저장 오류]", e)
            self.db.rollback()

    def save_history_team_chat_messages(self, user_id, team_id, messages, summary):
        try:
            with self.db.cursor() as cursor:
                for i in range(0, len(messages) - 1, 2):
                    if messages[i].type == "human":
                        user_msg = messages[i].content
                    else:
                        user_msg = ""

                    if messages[i + 1].type == "ai":
                        ai_msg = messages[i + 1].content
                    else:
                        ai_msg = ""

                    sql = """
                        INSERT INTO TeamQna_Table (Team_ID, Client_ID, conversation_id, Team_Asw, Team_Rsp)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (team_id, user_id, summary, user_msg, ai_msg))
            self.db.commit()
        except Exception as e:
            print("[팀 이전채팅 저장 오류]", e)
            self.db.rollback()

    def save_history_chat_messages(self, user_id, messages, summary):
        try:
            with self.db.cursor() as cursor:
                for i in range(0, len(messages) - 1, 2):
                    if messages[i].type == "human":
                        user_msg = messages[i].content
                    else:
                        user_msg = ""

                    if messages[i + 1].type == "ai":
                        ai_msg = messages[i + 1].content
                    else:
                        ai_msg = ""

                    sql = """
                        INSERT INTO Personal_Table (Client_ID, conversation_id, Personal_Asw, Personal_Rsp)
                        VALUES (%s, %s, %s, %s)
                    """
                    print(f"저장 예정: 질문={user_msg}, 답변={ai_msg}")
                    cursor.execute(sql, (user_id, summary, user_msg, ai_msg))

            self.db.commit()
        except Exception as e:
            print("[DB 저장 오류]", e)
            self.db.rollback()
