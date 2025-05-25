import pymysql
import os
from dotenv import load_dotenv

class TeamInvite:
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_pwd = os.getenv("DB_PWD")

    def connect_db(self):
        return pymysql.connect(
            host=self.db_host,
            port=int(self.db_port),
            user=self.db_user,
            password=self.db_pwd,
            db="test",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

    def invite_member(self, team_id, user_id, role):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            # 팀 정보 가져오기
            cursor.execute("SELECT * FROM Team_Table WHERE Team_ID = %s", (team_id,))
            team = cursor.fetchone()

            if not team:
                # 아직 팀 멤버 정보가 없으면 새로 생성 (최초 팀 생성자만 등록되어 있는 경우)
                cursor.execute("""
                    INSERT INTO Team_Table (Team_ID, ClientID_fir, ClientType_fir)
                    VALUES (%s, %s, %s)
                """, (team_id, user_id, role))
            else:
                # 비어있는 슬롯 찾기
                added = False
                for i in ["fir", "sec", "thr", "fou", "fiv", "six"]:
                    if not team[f"ClientID_{i}"]:
                        cursor.execute(f"""
                            UPDATE Team_Table
                            SET ClientID_{i} = %s, ClientType_{i} = %s
                            WHERE Team_ID = %s
                        """, (user_id, role, team_id))
                        added = True
                        break

                if not added:
                    print("⚠️ 팀 멤버 슬롯이 가득 찼습니다.")
                    conn.close()
                    return False

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print("❌ 팀원 초대 중 오류:", e)
            return False

    def get_user_teams(self, user_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            sql = """
                SELECT DISTINCT
                    c.Team_ID,
                    c.Team_Name,
                    c.Team_Description,
                    CASE
                        WHEN c.Created_By = %s THEN '생성자'
                        WHEN t.ClientID_fir = %s THEN t.ClientType_fir
                        WHEN t.ClientID_sec = %s THEN t.ClientType_sec
                        WHEN t.ClientID_thr = %s THEN t.ClientType_thr
                        WHEN t.ClientID_fou = %s THEN t.ClientType_fou
                        WHEN t.ClientID_fiv = %s THEN t.ClientType_fiv
                        WHEN t.ClientID_six = %s THEN t.ClientType_six
                        ELSE '팀원'
                    END AS Role
                FROM TeamCreate_Table c
                LEFT JOIN Team_Table t ON c.Team_ID = t.Team_ID
                WHERE (c.Created_By = %s OR %s IN (t.ClientID_fir, t.ClientID_sec, t.ClientID_thr, t.ClientID_fou, t.ClientID_fiv, t.ClientID_six))
                AND c.Team_Name IS NOT NULL
                AND c.Team_Name != ''
            """
            params = (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            print("❌ 사용자별 팀 목록 조회 오류:", e)
            return []


    def leave_team(self, user_id, team_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            for i in ["fir", "sec", "thr", "fou", "fiv", "six"]:
                cursor.execute(f"""
                    UPDATE Team_Table
                    SET ClientID_{i} = NULL, ClientType_{i} = NULL
                    WHERE Team_ID = %s AND ClientID_{i} = %s
                """, (team_id, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print("❌ 팀 나가기 오류:", e)
            return False
