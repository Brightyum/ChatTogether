from .db import Db


class UserQnaSave:
    def __init__(self):
        self.db = Db.getDb()

    def save_chat_messages(self, user_id, messages, summary):
        try:
            with self.db.cursor() as cursor:
                for msg in messages:
                    sql = """
                        INSERT INTO Personal_Table (Client_ID, conversation_id, sender, content)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(
                        sql,
                        (
                            user_id,
                            summary,  # 해당 세션의 요약 전체로 동일하게
                            msg.type,
                            msg.content,
                        ),
                    )
            self.db.commit()
        except Exception as e:
            print("[DB 저장 오류]", e)
            self.db.rollback()
