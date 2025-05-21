import sys
import os

# app.py 맨 위에 추가
from DataBase.db_base import get_connection
#테스트

# 루트 디렉토리 경로를 PYTHONPATH에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    Response,
    stream_with_context,
)

from RAG.LLM.chat_system import ChatSystem

# from db.client_model import insert_client  # DB 처리 함수 임포트

app = Flask(__name__)

app.secret_key = 'your-secret-key' 

chat_system = ChatSystem()
# 에러 추적 용이
app.config["PROPAGATE_EXCEPTIONS"] = True


# 메인페이지
@app.route("/")
def home():
    return render_template("index.html")


# 회원가입 페이지
@app.route("/signup", methods=["GET"])
def signup_form():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_submit():
    client_id = request.form["client_id"]
    password = request.form["client_pass"]  
    #password_confirm = request.form["password_confirm"] #비밀번호 확인값

    client_name = request.form["client_name"]
    client_age = request.form["client_age"]
    client_gender = request.form["client_gender"]
    client_email = request.form["client_email"]

     #  필수 항목 누락 시
    if not all([client_id, password, client_name, client_age, client_gender, client_email]):
        flash("모든 항목을 입력해주세요.")
        return render_template("signup.html")
    
    

    
    flash('회원가입이 완료되었습니다.로그인 페이지로 이동합니다.')
    return render_template("signup_success.html")
    

#아이디 중복확인
@app.route('/check_id')
def check_id():
    client_id = request.args.get('client_id')


    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM client_table WHERE Client_ID = %s"
            cursor.execute(sql, (client_id,))
            result = cursor.fetchone()

            return jsonify({'exists': bool(result)})
    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        conn.close()


# 로그인 페이지
@app.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")


# 질의응답 페이지 보여주기
@app.route("/qa", methods=["GET"])
def qa_page():
    question = request.args.get("question", "")
    return render_template("qa.html", question=question)

# 질의응답
@app.route("/stream-ask", methods=["POST"])
def stream_ask():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "질문칸을 채워주세요"}), 400

    return Response(
        stream_with_context(chat_system.run(question)), content_type="text/plain"
    )


# 프롬프트 추가 페이지
@app.route("/add_prompt", methods=["GET", "POST"])
def add_prompt():
    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        content = request.form["content"]
        # TODO: DB에 저장 로직 구현
        flash("프롬프트가 성공적으로 추가되었습니다!")
        return redirect(url_for("add_prompt"))
    return render_template("add_prompt.html")


# 팀원 초대 페이지
@app.route("/invite_member", methods=["GET", "POST"])
def invite_member():
    team_list = ["팀 A", "팀 B", "팀 C"]  # 실제 프로젝트에선 DB에서 불러오기
    if request.method == "POST":
        team = request.form["team"]
        email = request.form["email"]
        role = request.form["role"]
        # TODO: 초대 처리 및 DB 연동
        flash(f"{email} 님을 {team} 팀에 {role} 권한으로 초대했습니다.")
        return redirect(url_for("invite_member"))
    return render_template("invite_member.html", team_list=team_list)


#가격 페이지지
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')



# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)
