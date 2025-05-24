<<<<<<< HEAD
from flask import Flask, request, render_template, redirect, url_for, session, flash
import pymysql

app = Flask(__name__)
app.secret_key = 'secret_key'  # 여긴 뭘 넣어야될까여

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client_id = request.form['client_id']
        client_pass = request.form['client_pass']

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='@sjh9300',
            db='ddongdb',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with conn.cursor() as cursor:
                #아이디가 존재하는지 먼저 확인
                cursor.execute("SELECT * FROM client_table WHERE Client_ID = %s", (client_id,))
                user = cursor.fetchone()

                if not user:
                    flash("존재하지 않는 사용자입니다.")
                    return render_template('login.html')

                #아이디는 존재하지만 비번이 다른 경우
                if user['Client_Pass'] != client_pass:
                    flash("비밀번호가 일치하지 않습니다.")
                    return render_template('login.html')

                #로그인 성공
                session['client_id'] = user['Client_ID']
                flash("로그인 완료")
                return redirect(url_for('home'))

        finally:
            conn.close()
    return render_template('login.html')
=======
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
                sql = "SELECT * FROM Client_Table WHERE Client_ID = %s AND Client_Pass = %s"
                cursor.execute(sql, (user_id, user_pass))
                result = cursor.fetchone()

            if result:
                return True
            else:
                return False

        except Exception as e:
            print(f"[로그인 오류] {e}")
            return None

        finally:
            if 'conn' in locals() and conn:
                conn.close()



>>>>>>> 0f9c48d40657963ef648174a0ad6aead7c5933b3
