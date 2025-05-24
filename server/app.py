from flask import Flask, render_template, request, redirect, url_for, jsonify,flash
from DataBase.Login_function import LoginFunction

app = Flask(__name__)

app.secret_key = 'your-secret-key' 


lg = LoginFunction()

# 메인페이지
@app.route('/')
def home():
    return render_template('index.html')

# 회원가입 페이지
@app.route('/signup', methods=['GET'])
def signup_form():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_submit():

    client_id = request.form['client_id']
    password = request.form['password']
    password_check = request.form['password_check']
    phone = request.form['phone']
    school = request.form['school']
    

@app.route('/check_id')
def check_id():
    import pymysql
    client_id = request.args.get('client_id')

    try:
        conn = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_pwd,
            db="Client_Table",
            charset="utf8"
        )
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Client_Table WHERE Client_ID = %s"
            cursor.execute(sql, (client_id,))
            user = cursor.fetchone()

            if user:
                return jsonify({'available': False})  # 이미 있음
            else:
                return jsonify({'available': True})   # 사용 가능

    except Exception as e:
        print("ID 중복 확인 오류:", e)
        return jsonify({'available': False})

    finally:
        if 'conn' in locals():
            conn.close()


    # 비밀번호 확인
    if password != password_check:
        flash("비밀번호가 서로 일치하지 않습니다.")
        return render_template('signup.html')

    result = insert_client(client_id, password, phone, school)

    if result:
        return redirect(url_for('login_form'))
    else:
        flash("회원가입 중 오류가 발생했습니다.")
        return render_template('signup.html')

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']

        if not user_id or not user_pass:
            flash("아이디와 비밀번호를 모두 입력하세요.")
            return render_template('login.html')

        try:
            result = lg.verify_user_credentials(user_id, user_pass) #사용자 로그인 정보가 데이터베이스에 존재하는지 검증하는 함수

            if result is True:
                return render_template('index.html', username=user_id)
            elif result is False:
                flash("아이디 또는 비밀번호가 일치하지 않습니다.")
            else:  # None 반환 시 DB 오류
                flash("로그인 중 서버 오류가 발생했습니다.")

            return render_template('login.html')
        except Exception as e:
            print(e)
    return render_template('login.html')

# 질의응답 페이지 보여주기
@app.route('/qa', methods=['GET'])
def qa_page():
    question = request.args.get('question', '')
    return render_template('qa.html', question=question)

# 질문을 받아 답변을 반환하는 API (db나 랭체인하는 사람 보고 알아서서)
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()

    question = data.get('question', '')


    # LangChain 또는 DB 처리 로직 삽입
    # 예시: answer = get_answer_from_llm(question)
    answer = f"‘{question}’에 대한 테스트 응답입니다."

    return jsonify({'answer': answer})

# 서버 실행

if __name__ == '__main__':
    app.run(port=5001)

