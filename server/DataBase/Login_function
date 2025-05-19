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
