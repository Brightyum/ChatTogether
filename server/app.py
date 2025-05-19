from flask import Flask, render_template, request, redirect, url_for, jsonify
#from db.client_model import insert_client  # DB 처리 함수 임포트

app = Flask(__name__)

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
    phone = request.form['phone']
    school = request.form['school']
    #insert_client(client_id, password, phone, school)   #insert_client는 임의로 이름 지은거라 바꿔도 됨
    return redirect(url_for('login_form'))

# 로그인 페이지
@app.route('/login', methods=['GET'])
def login_form():
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
    app.run(debug=True)
