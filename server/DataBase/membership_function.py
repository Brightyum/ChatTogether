import pymysql
import os
import secrets
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
            db="test",  # DB 이름 확인
            charset="utf8",
        )

    def process_signup(
        self,
        client_id,
        password,
        password_check,
        name,
        old,
        gender,
        email,
        phone,
        school,
    ):
        # 필수값 확인
        if not all(
            [
                client_id,
                password,
                password_check,
                name,
                old,
                gender,
                email,
                phone,
                school,
            ]
        ):
            return False, "모든 항목을 입력해주세요."

        if password != password_check:
            return False, "비밀번호가 서로 일치하지 않습니다."

        api_key = secrets.token_hex(16)  # API 키 생성
        default_permission = "USER"

        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO Client_Table (
                        Client_ID, Client_Pass, Client_Name, Client_Old, Client_Gen,
                        Client_Eml, Client_Num, Client_Sch, Client_Per, Client_API
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(
                    sql,
                    (
                        client_id,
                        password,
                        name,
                        old,
                        gender,
                        email,
                        phone,
                        school,
                        default_permission,
                        api_key,
                    ),
                )
            conn.commit()
            return True, "회원가입 성공"

        except Exception as e:
            print("[회원가입 오류]:", e)
            return False, "오류가 발생했습니다 다시 실행해주세요"

        finally:
            if "conn" in locals() and conn:
                conn.close()

    def check_duplicate_id(self, client_id):
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = "SELECT 1 FROM Client_Table WHERE Client_ID = %s"
                cursor.execute(sql, (client_id,))
                user = cursor.fetchone()
                if user:
                    return {
                        "available": False,
                        "message": "이미 존재하는 아이디입니다.",
                    }
                else:
                    return {"available": True, "message": "사용 가능한 아이디입니다."}
        except Exception as e:
            print("[ID 중복 확인 오류]:", e)
            return {"available": False, "message": "서버 오류가 발생했습니다."}
        finally:
            if "conn" in locals() and conn:
                conn.close()
