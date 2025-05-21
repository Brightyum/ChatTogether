import pymysql
import os
from dotenv import load_dotenv

class MembershipFunction:
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_pwd = os.getenv("DB_PWD")

    def get_connection(self):
        return pymysql.connect(
            host=self.db_host,
            port=int(self.db_port),
            user=self.db_user,
            password=self.db_pwd,
            db="test",
            charset="utf8"
        )

    def process_signup(self, client_id, password, password_check, phone, school, gender, email):
        if not all([client_id, password, password_check, phone, school]):
            return False, "모든 항목을 입력해주세요."

        if password != password_check:
            return False, "비밀번호가 서로 일치하지 않습니다."

        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO Client_Table (
                        Client_ID, Client_Pass, Client_Num, Client_Sch, Client_Gen, Client_Eml, Client_per, Client_API
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    client_id, password, phone, school, gender, email , "USER", "INACTIVE"
                ))
            conn.commit()
            return True

        except Exception as e:
            print("[회원가입 오류]:", e)
            return False

        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def check_duplicate_id(self, client_id):
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = "SELECT * FROM Client_Table WHERE Client_ID = %s"
                cursor.execute(sql, (client_id,))
                user = cursor.fetchone()
                return {"available": False} if user else {"available": True}

        except Exception as e:
            print("[ID 중복 확인 오류]:", e)
            return {"available": False}

        finally:
            if 'conn' in locals() and conn:
                conn.close()
