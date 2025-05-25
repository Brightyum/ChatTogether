import pymysql
import os
from dotenv import load_dotenv

class UserDB:
    def __init__(self):
        load_dotenv()
        self.conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PWD"),
            db=os.getenv("DB_NAME"),
            charset="utf8"
        )
        self.cursor = self.conn.cursor()

    def get_user_info(self, client_id):
        sql = """
            SELECT Client_ID, Client_Name, Client_Pass, Client_Old, Client_Gen,
            Client_Eml, Client_Num, Client_Sch, Client_plan
            FROM Client_Table
            WHERE Client_ID = %s
        """
        self.cursor.execute(sql, (client_id))
        return self.cursor.fetchone()
    
        if result:
                return {
                    "user_id": result[0],
                    "name": result[1],
                    "password": result[2],
                    "old": result[3],
                    "gender": result[4],
                    "email": result[5],
                    "phone": result[6],
                    "school": result[7],
                    "plan": result[8],
                } 
        return None


    def update_user_info(self, client_id, name=None, email=None, phone=None, school=None, password=None, old=None, gender=None):
        updates = []
        params = []

        if name:
            updates.append("Client_Name = %s")
            params.append(name)
        if email:
            updates.append("Client_Eml = %s")
            params.append(email)
        if phone:
            updates.append("Client_Num = %s")
            params.append(phone)
        if school:
            updates.append("Client_Sch = %s")
            params.append(school)
        if password:
            updates.append("Client_Pass = %s")
            params.append(password)
        if old:
            updates.append("Client_Old = %s")
            params.append(old)
        if gender:
            updates.append("Client_Gen = %s")
            params.append(gender)

        if not updates:
            return False

        sql = f"UPDATE Client_Table SET {', '.join(updates)} WHERE Client_ID = %s"
        params.append(client_id)

        self.cursor.execute(sql, params)
        self.conn.commit()

        affected_rows = self.cursor.rowcount

        return affected_rows > 0

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    #요금제 업데이트
    def update_user_plan(self, client_id, plan):
        sql = "UPDATE Client_Table SET Client_Plan = %s WHERE Client_ID = %s"
        self.cursor.execute(sql, (plan, client_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

