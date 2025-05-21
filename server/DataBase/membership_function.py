import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_user = os.getenv("DB_USER")
db_pwd = os.getenv("DB_PWD")

def insert_client(client_id, password, phone, school):
    try:
        conn = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_pwd,
            db="test",  # 실제 DB명
            charset="utf8"
        )

        with conn.cursor() as cursor:
            sql = """
                INSERT INTO Client_Table (
                    Client_ID, Client_Pass, Client_Phone, Client_School, Client_Per, Client_API
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            default_per = "USER"
            default_api = "INACTIVE"

            cursor.execute(sql, (
                client_id, password, phone, school, default_per, default_api
            ))

        conn.commit()
        return True

    except Exception as e:
        print("[회원가입 오류]:", e)
        return False

    finally:
        if 'conn' in locals() and conn:
            conn.close()
