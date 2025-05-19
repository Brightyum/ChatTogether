@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        client_id = request.form['client_id']
        client_pass = request.form['client_pass']
        client_name = request.form['client_name']
        client_age = request.form['client_age']
        client_gender = request.form['client_gender']
        client_email = request.form['client_email']

        # 기본 검증
        if not all([client_id, client_pass, client_name, client_age, client_gender, client_email]):
            flash("모든 항목을 입력해주세요.")
            return render_template('signup.html')

        if client_gender not in ['남성', '여성']:
            flash("성별은 M 또는 F로 입력해주세요.")
            return render_template('signup.html')

        try:
            client_age = int(client_age)
        except ValueError:
            flash("나이는 숫자만 입력해주세요.")
            return render_template('signup.html')

        # DB 연결
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='mysql',
            db='ddongdb',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            with conn.cursor() as cursor:
                # 아이디 중복 확인
                cursor.execute("SELECT * FROM client_table WHERE Client_ID = %s", (client_id,))
                if cursor.fetchone():
                    flash("이미 존재하는 아이디입니다.")
                    return render_template('signup.html')

                # 이메일 중복 확인 (선택)
                cursor.execute("SELECT * FROM client_table WHERE Client_Email = %s", (client_email,))
                if cursor.fetchone():
                    flash("이미 사용 중인 이메일입니다.")
                    return render_template('signup.html')

                # 최종 INSERT
                cursor.execute("""
                    INSERT INTO client_table (
                        Client_ID, Client_Pass, Client_Name,
                        Client_Age, Client_Gender, Client_Email, Client_Join
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (client_id, client_pass, client_name, client_age, client_gender, client_email))

                conn.commit()
                flash("회원가입이 완료되었습니다.")
                return redirect(url_for('login.html'))
        finally:
            conn.close()
    return render_template('login.html')
