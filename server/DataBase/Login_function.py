import pymysql
import os
from dotenv import load_dotenv

class LoginFunction():
    def __init__(self):                        
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_pwd = os.getenv("DB_PWD")
        
    def verify_user_credentials(self, user_id, user_pass):
        try:
            conn = pymysql.connect(
                host=self.db_host,
                port=int(self.db_port),
                user=self.db_user,
                password=self.db_pwd,
                db="test",  # DB 이름은 실제 사용 중인 DB 이름으로 변경
                charset="utf8"
            )

            with conn.cursor() as cursor:
                #sql = "SELECT * FROM Client_Table WHERE Client_ID = %s AND Client_Pass = %s"
                #이름 가져오기 추가
                sql = """
                SELECT Client_ID, Client_Name       
                FROM Client_Table
                WHERE Client_ID = %s AND Client_Pass = %s
                """
                cursor.execute(sql, (user_id, user_pass))
                result = cursor.fetchone()

            if result:
                return {"user_id": result[0], "user_name": result[1]}
            else:
                return False

        except Exception as e:
            print(f"[로그인 오류] {e}")
            return None

        finally:
            if 'conn' in locals() and conn:
                conn.close()



