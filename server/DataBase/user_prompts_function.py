from .db import Db
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# 사용자 프롬프트를 데이터베이스에 저장
class UserPrompt:

    def __init__(self):
        self.db = Db().getDb()

    def savePrompt(self, user_id, title, category, content):
        prompt_text = f"[{category}] {title} - {content}"
        try:
            with self.db.cursor() as cursor:

                sql_user = """
                    INSERT INTO user_prompts (Personal_ID, title, category, content, prompt_text)
                    VALUES (%s, %s, %s, %s, %s)
                 """
                cursor.execute(
                    sql_user, (user_id, title, category, content, prompt_text)
                )

                self.db.commit()
                return True
        except Exception as e:
            print("db저장 오류", e)
            self.db.rollback()
            return False
        finally:
            self.db.close()

    def getPrompt(self, user_id=None):
        prompt = []

        try:
            with self.db.cursor() as cursor:
                if user_id:
                    sql_user = """
                        SELECT title, category, content
                        FROM user_prompts
                        WHERE Personal_ID = %s
                        ORDER BY created_at
                    """
                    cursor.execute(sql_user, (user_id,))
                    prompt = cursor.fetchall()
                    return prompt
        except Exception as e:
            print("db 로딩 오류", e)
            return []
        finally:
            try:
                self.db.close()
            except:
                pass
