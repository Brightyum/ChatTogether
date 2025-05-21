import uuid
from flask import Flask, request, render_template, redirect, url_for, flash
import pymysql
import os
from dotenv import load_dotenv

# env파일에서 민감한 정보를 저장하고 os.getenv()로 호출
load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_user = os.getenv("DB_USER")
db_pwd = os.getenv("DB_PWD")

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 사용자 입력
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']
        user_sch = request.form['user_sch']
        user_eml = request.form['user_eml']
        user_num = request.form['user_num']
        user_per = request.form['user_per']  # 사용자 직접 입력
        user_gen = request.form['user_gen']

        # 자동 생성
        client_api = str(uuid.uuid4())[:60]  # 60자 이하

        # 필수값 확인
        if not all([user_id, user_pass, user_sch, user_eml, user_per, user_gen]):
            flash("모든 필수 항목을 입력하세요.")
            return render_template('signup.html')

        try:
            conn = pymysql.connect(
        host=db_host,  # 호스트 ip(외부 데이터베이스 서버 ip)
        port=(db_port),  # 데이터베이스 외부 포트
        user=db_user,  # 데이터베이스 사용자 이름
        password=db_pwd,  # 데이터베이스 사용자 비밀번호
        db="Client_Table",  # 데이터베이스 테이블 이름
        charset="utf8",  # 한국어 안깨지도록 설정
        )

            with conn.cursor() as cursor:
                # ID 중복 체크
                cursor.execute("SELECT * FROM Client_Table WHERE Client_ID = %s", (user_id,))
                if cursor.fetchone():
                    flash("이미 존재하는 아이디입니다.")
                    return render_template('register.html')

                sql = """
                INSERT INTO Client_Table 
                (Client_ID, Client_Pass, Client_Sch, Client_API, Client_Eml, Client_Num, Client_Per, Client_Gen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    user_id, user_pass, user_sch, client_api, user_eml, user_num, user_per, user_gen
                ))
                conn.commit()
                flash("회원가입이 완료되었습니다.")
                return redirect(url_for('login'))

        except Exception as e:
            print("회원가입 오류:", e)
            flash("회원가입 중 문제가 발생했습니다.")
            return render_template('index.html')

        finally:
            conn.close()

    return render_template('index.html')
