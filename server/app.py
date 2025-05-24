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
    session,
    send_file,
)
from DataBase.Login_function import LoginFunction
from DataBase.user_prompts_function import UserPrompt
from DataBase.membership_function import MembershipFunction
from DataBase.Personal_qna import PersonalQnaExporter
from datetime import datetime
from DataBase.Create_Team import TeamCreator
import sys
import os

from DataBase.user_db import UserDB

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from RAG.LLM.chat_system import ChatSystem

app = Flask(__name__)

app.secret_key = "your-secret-key"

# 에러 추적 용이
app.config["PROPAGATE_EXCEPTIONS"] = True

lg = LoginFunction()
membership = MembershipFunction()

# 메인페이지
@app.route("/")
def home():
    return render_template("index.html")


# 회원가입 페이지
@app.route("/signup", methods=["GET"])
def signup_form():
    return render_template("signup.html")

# 회원가입 폼 처리
@app.route("/signup", methods=["POST"])
def signup_submit():

    client_id = request.form["client_id"]
    password = request.form["password"]
    password_check = request.form["password_check"]
    name = request.form["client_name"]        # 이름 추가
    old = request.form["client_old"]          # 나이 추가
    gender = request.form["client_gender"]
    email = request.form["client_email"]
    phone = request.form["phone"]
    school = request.form["school"]


    # process_signup의 인자 순서와 맞춤
    success, message = membership.process_signup(
        client_id, password, password_check, name, old, gender, email, phone, school
    )

    if success:
        return render_template("signup_success.html")
    else:
        return render_template("signup.html")


#중복 확인
@app.route("/check_id")
def check_id():
   client_id = request.args.get("client_id")
   return jsonify(membership.check_duplicate_id(client_id))



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

            if result:
                session["user_id"] = user_id  # 사용자 아이디값 세션에 저장
                session["user_name"] = result["user_name"]  # 이름 저장
                flash(f"{result['user_name']}님 환영합니다.")
                return render_template("index.html", username=user_id)
            elif result is False:
                flash("아이디 또는 비밀번호가 일치하지 않습니다.")
            else:  # None 반환 시 DB 오류
                flash("로그인 중 서버 오류가 발생했습니다.")

            return render_template("login.html")
        except Exception as e:
            print(e)
    return render_template("login.html")

# 로그아웃 페이지
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

#질의응답 페이지 보여주기
@app.route("/qa", methods=["GET"])
def qa_page():
    user_id = session.get("user_id")
    question = request.args.get("question", "")
    mode = request.args.get("mode", "personal")
    team_id = request.args.get("team_id")

     # 팀 목록: (더미 데이터, 추후 DB 연동 예정)
    dummy_teams = [{"id": 1, "name": "팀 A (더미)"}, {"id": 2, "name": "팀 B (더미)"}]

# 팀 모드 처리: team_id 유효성 확인
    if mode == "team" and team_id:
        try:
            team_id = int(team_id)
        except ValueError:
            return "잘못된 팀 ID입니다.", 400

        if not any(team["id"] == team_id for team in dummy_teams):
            return "권한이 없는 팀입니다.", 403
    else:
        team_id = None  # 개인 모드일 때는 team_id 없음


    return render_template("qa.html", question=question,
        mode=mode,
        team_id=team_id,
        teams=dummy_teams  # 팀 목록 전달
)


# 질의응답
@app.route("/stream-ask", methods=["POST"])
def stream_ask():
    data = request.get_json()

    question = data.get("question", "").strip()

    user_id = session.get("user_id")

    mode = data.get("mode", "personal")

    team_id = data.get("team_id")

    
    if not user_id:
        return jsonify({"error": "로그인이 필요합니다"}), 401  

    if not question:
        return jsonify({"error": "질문칸을 채워주세요"}), 400
    
    # 팀 모드 처리: team_id 전달
    if mode == "team" and team_id:
        try:
            team_id = int(team_id)
        except ValueError:
            return jsonify({"error": "잘못된 팀 ID입니다."}), 400
        chat_system = ChatSystem(user_id=user_id, team_id=team_id)
    else:
        chat_system = ChatSystem(user_id=user_id)

    return Response(
        stream_with_context(chat_system.run(question)), content_type="text/plain"
    )

prompt_list = []

# #  디비 저장 관련 추가 코드
# @app.route("/save_qa", methods=["POST"])
# def save_qa():
#     data = request.get_json()
#     question = data.get("question", "").strip()
#     response = data.get("response", "").strip()

#     if not question or not response:
#         return jsonify({"error": "질문과 응답이 모두 필요합니다."}), 400

#     user_id = session.get("user_id")
#     if not user_id:
#         return jsonify({"error": "로그인이 필요합니다."}), 401

#     # 대화 요약: 지금은 임시로 질문 앞부분 사용
#     topic = question[:20] + "..." if len(question) > 20 else question

#     qna = PersonalQnaExporter()
#     success = qna.save_to_db(user_id, question, response, topic_summary=topic)

#     if success:
#         return jsonify({"success": True})
#     else:
#         return jsonify({"error": "저장에 실패했습니다."}), 500

@app.route("/export_qna_json")
def export_qna_json():
    try:
        exporter = PersonalQnaExporter()
        exporter.export_to_json()
        flash("QnA 데이터를 JSON으로 성공적으로 저장했습니다.")
        return redirect(url_for("qa_page"))
    except Exception as e:
        print("에러 발생:", e)
        flash("JSON 저장 중 오류가 발생했습니다.")
        return redirect(url_for("qa_page"))



# 프롬프트 추가 페이지
@app.route("/add_prompt", methods=["GET", "POST"])
def add_prompt():
    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        content = request.form["content"]

        user_id = session.get("user_id")

        prompt_list.append({"title": title, "category": category, "content": content})

        if not user_id:
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))  # 되돌아가는 코드인데 잘 모름 - 염승욱

        # result = chat_system.get_prompt(prompt_list)
        # TODO: DB에 저장 로직 구현
        prompt_db = UserPrompt()
        prompt_db.savePrompt(user_id, title, category, content)

        # DB에서 가져오기

        flash("프롬프트가 성공적으로 추가되었습니다!")

        # print(result)

        return redirect(url_for("add_prompt"))
    return render_template("add_prompt.html")

# 팀 생성 페이지
@app.route("/create_team", methods=["GET", "POST"])
def create_team():
    if request.method == "POST":
        try:
            team_name = request.form["team_name"]
            team_desc = request.form["team_desc"]

            created_by = session.get("user_id")
            if not created_by:
                flash("로그인이 필요합니다.")
                return redirect(url_for("login"))

            team_creator = TeamCreator()
            success = team_creator.create_team(team_name, team_desc, created_by)

            if success:
                flash(f"팀 '{team_name}'이(가) 성공적으로 생성되었습니다.")
                return redirect(url_for("qa_page"))
            else:
                flash("팀 생성 중 오류가 발생했습니다.")
                return render_template("create_team.html")

        except Exception as e:
            print(f"팀 생성 중 에러 발생: {e}")
            flash("서버 오류가 발생했습니다.")
            return render_template("create_team.html")

    return render_template("create_team.html")


@app.route("/qa2")
def qa_page_teams():
    team_creator = TeamCreator()
    team_list = team_creator.get_all_teams()  # DB에서 팀 목록 가져오기
    return render_template("qa.html", teams=team_list)


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



# 사용자 정보 페이지
@app.route("/profile", methods=["GET"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = UserDB()
    user = db.get_user_info(session["user_id"])
    return render_template("profile.html", user=user)


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    client_id = session["user_id"]
    name = request.form.get("name")
    password = request.form.get("password")
    old = request.form.get("client_old")
    gender = request.form.get("client_gender")
    email = request.form.get("email")
    phone = request.form.get("phone")
    school = request.form.get("school")

    db = UserDB()
    success = db.update_user_info(
        client_id=session["user_id"],
        name=name,
        email=email,
        phone=phone,
        school=school,
        password=password,
        old=old,
        gender=gender,
    )

    if success:
        flash("정보가 성공적으로 수정되었습니다.")
    else:
        flash("변경된 항목이 없습니다.")

    return redirect(url_for("mypage"))


# 마이페이지
@app.route("/mypage")
def mypage():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = UserDB()
    user = db.get_user_info(session["user_id"])
    return render_template("mypage.html", user=user)




# 서버 실행
if __name__ == "__main__":

    app.run(port=5001)


