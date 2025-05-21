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
from DataBase.Login_function import LoginFunction
from RAG.LLM.chat_system import ChatSystem

app = Flask(__name__)

app.secret_key = "your-secret-key"

chat_system = ChatSystem()
# 에러 추적 용이
app.config["PROPAGATE_EXCEPTIONS"] = True

lg = LoginFunction()


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
    password = request.form["password"]
    password_check = request.form["password_check"]
    phone = request.form["phone"]
    school = request.form["school"]


@app.route("/check_id")
def check_id():
    import pymysql

    client_id = request.args.get("client_id")

    try:
        conn = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_pwd,
            db="Client_Table",
            charset="utf8",
        )
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Client_Table WHERE Client_ID = %s"
            cursor.execute(sql, (client_id,))
            user = cursor.fetchone()

            if user:
                return jsonify({"available": False})  # 이미 있음
            else:
                return jsonify({"available": True})  # 사용 가능

    except Exception as e:
        print("ID 중복 확인 오류:", e)
        return jsonify({"available": False})

    finally:
        if "conn" in locals():
            conn.close()

    # 비밀번호 확인
    if password != password_check:
        flash("비밀번호가 서로 일치하지 않습니다.")
        return render_template("signup.html")

    result = insert_client(client_id, password, phone, school)

    if result:
        return redirect(url_for("login_form"))
    else:
        flash("회원가입 중 오류가 발생했습니다.")
        return render_template("signup.html")


# 로그인 페이지
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["user_id"]
        user_pass = request.form["user_pass"]

        if not user_id or not user_pass:
            flash("아이디와 비밀번호를 모두 입력하세요.")
            return render_template("login.html")

        try:
            result = lg.verify_user_credentials(
                user_id, user_pass
            )  # 사용자 로그인 정보가 데이터베이스에 존재하는지 검증하는 함수

            if result is True:
                return render_template("index.html", username=user_id)
            elif result is False:
                flash("아이디 또는 비밀번호가 일치하지 않습니다.")
            else:  # None 반환 시 DB 오류
                flash("로그인 중 서버 오류가 발생했습니다.")

            return render_template("login.html")
        except Exception as e:
            print(e)
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


prompt_list = []


# 프롬프트 추가 페이지
@app.route("/add_prompt", methods=["GET", "POST"])
def add_prompt():
    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        content = request.form["content"]

        prompt_list.append({"title": title, "category": category, "content": content})

        result = chat_system.get_prompt(prompt_list)
        # TODO: DB에 저장 로직 구현
        flash("프롬프트가 성공적으로 추가되었습니다!")
        print(result)

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


# 가격 페이지지
@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


# 서버 실행
if __name__ == "__main__":
    app.run(port=5001)
