from .db import Db
import pymysql
from dotenv import load_dotenv
import os


class UserQnaList:
    def __init__(self):
        load_dotenv()

    def get_conversation_ids(self, user_id):
        try:
            with pymysql.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PWD"),
                port=int(os.getenv("DB_PORT")),
                database=os.getenv("DB_NAME"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            ) as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT conversation_id, MAX(created_at) as latest_time
                        FROM Personal_Table
                        WHERE Client_ID = %s
                        GROUP BY conversation_id
                        ORDER BY latest_time DESC
                    """
                    cursor.execute(sql, (user_id,))
                    result = cursor.fetchall()

                    conversation_ids = [
                        row["conversation_id"]
                        for row in result
                        if row.get("conversation_id")
                    ]
                    return conversation_ids

        except Exception as e:
            print("[conversation_id 탐색 오류]", e)
            return []

    def get_conversation_data(self, user_id, topic):
        conn = None
        try:
            with pymysql.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PWD"),
                port=int(os.getenv("DB_PORT")),
                database=os.getenv("DB_NAME"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            ) as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT Personal_Asw, Personal_Rsp, created_at
                        FROM Personal_Table
                        WHERE Client_ID = %s AND conversation_id = %s
                        ORDER BY created_at ASC
                    """
                    cursor.execute(sql, (user_id, topic))
                    result = cursor.fetchall()

                    return result

        except Exception as e:
            print("[대화 기록 탐색 오류]", e)
            return []
