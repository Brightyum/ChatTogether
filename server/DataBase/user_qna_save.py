from .db import Db


class UserQnaSave:
    def __init__(self):
        self.db = Db.getDb()

    def save_chat_messages(self, user_id, question, answer, summary):
        try:
            with self.db.cursor() as cursor:
                sql = """
                    INSERT INTO Personal_Table (Client_ID, conversation_id, Personal_Rsp, Personal_Asw)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, summary, question, answer))
            self.db.commit()
        except Exception as e:
            print("[단일 QnA 저장 오류]", e)
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
                    cursor.execute(sql, (user_id, summary, user_msg, ai_msg))

            self.db.commit()
        except Exception as e:
            print("[DB 저장 오류]", e)
            self.db.rollback()
