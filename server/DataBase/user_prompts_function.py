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
    
    #프롬프트 수정 메서드
    def updatePrompt(self, user_id, original_title, new_title, category, content):
        try:
            with self.db.cursor() as cursor:
                sql = """
                    UPDATE user_prompts
                    SET title = %s, category = %s, content = %s, prompt_text = %s
                    WHERE Personal_ID = %s AND title = %s
                """
                prompt_text = f"[{category}] {new_title} - {content}"
                cursor.execute(sql, (new_title, category, content, prompt_text, user_id, original_title))
                self.db.commit()
                return True
        except Exception as e:
            print("프롬프트 수정 오류:", e)
            self.db.rollback()
            return False

    #프롬프트 삭제 메서드
    def deletePrompt(self, user_id, title):
        try:
            with self.db.cursor() as cursor:
                sql = "DELETE FROM user_prompts WHERE Personal_ID = %s AND title = %s"
                cursor.execute(sql, (user_id, title))
                self.db.commit()
                return True
        except Exception as e:
            print("프롬프트 삭제 오류:", e)
            self.db.rollback()
            return False
    
    #프롬프트 상세 정보를 읽어오는 메서드
    def getPromptByTitle(self, user_id, title):
        try:
            with self.db.cursor() as cursor:
                sql = "SELECT title, category, content FROM user_prompts WHERE Personal_ID = %s AND title = %s"
                cursor.execute(sql, (user_id, title))
                return cursor.fetchone()
        except Exception as e:
            print("프롬프트 조회 오류:", e)
            return None

