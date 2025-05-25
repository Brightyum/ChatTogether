import pymysql
import os
from dotenv import load_dotenv

class TeamCreator:
    def __init__(self):                        
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_pwd = os.getenv("DB_PWD")
        # DB 연결과 커서는 여기서 열지 말고 필요할 때 열고 닫는 게 안전

    def connect_db(self):
        return pymysql.connect(
            host=self.db_host,
            port=int(self.db_port),
            user=self.db_user,
            password=self.db_pwd,
            db="test",  # 실제 DB 이름으로 변경
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

    def verify_user_credentials(self, user_id, user_pass):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            # 사용자 검증 쿼리 예시 (필요에 따라 수정)
            sql = "SELECT * FROM users WHERE user_id=%s AND user_pass=%s"
            cursor.execute(sql, (user_id, user_pass))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        except Exception as e:
            print("❌ 사용자 인증 중 오류:", e)
            return False

    def get_next_team_id(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(Team_ID) AS max_id FROM TeamCreate_Table")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return (result["max_id"] or 0) + 1
        except Exception as e:
            print("❌ 다음 팀 ID 조회 중 오류:", e)
            return 1  # 기본값

    def create_team(self, team_name, team_desc, created_by):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            team_id = self.get_next_team_id()
            sql = """
                INSERT INTO TeamCreate_Table (Team_ID, Team_Name, Team_Description, Created_At, Created_By)
                VALUES (%s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql, (team_id, team_name, team_desc, created_by))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print("❌ 팀 생성 중 오류:", e)
            return False

    def get_user_teams(self, user_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            sql = "SELECT Team_ID AS id, Team_Name AS name FROM TeamCreate_Table WHERE Created_By = %s"
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            print("❌ 사용자별 팀 목록 불러오기 오류:", e)
            return []
