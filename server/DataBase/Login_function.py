from flask import Flask, render_template, request, redirect, url_for, flash
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
app.secret_key = 'your_secret_key'  # flash 메시지용

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']

        if not user_id or not user_pass:
            flash("아이디와 비밀번호를 모두 입력하세요.")
            return render_template('login.html')

        try:
            conn = pymysql.connect(
            host=db_host,  # 호스트 ip(외부 데이터베이스 서버 ip)
            port=int(db_port),  # 데이터베이스 외부 포트
            user=db_user,  # 데이터베이스 사용자 이름
            password=db_pwd,  # 데이터베이스 사용자 비밀번호
            db="Client_Table",  # 데이터베이스 테이블 이름
            charset="utf8",  # 한국어 안깨지도록 설정
            )

            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM Client_Table 
                WHERE Client_ID = %s AND Client_Pass = %s
                """
                cursor.execute(sql, (user_id, user_pass))
                user = cursor.fetchone()

                if user:
                    # 로그인 성공 → index.html로 이동
                    return render_template('index.html', username=user_id)
                else:
                    # 로그인 실패
                    flash("아이디 또는 비밀번호가 일치하지 않습니다.")
                    return render_template('login.html')

        except Exception as e:
            print("DB 오류:", e)
            flash("로그인 중 오류가 발생했습니다.")
            return render_template('login.html')

        finally:
            conn.close()

    # GET 요청이면 그냥 로그인 페이지 보여줌
    return render_template('login.html')
