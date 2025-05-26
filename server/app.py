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
from DataBase.TeamQnaExporter import TeamQnaExporter
from datetime import datetime
from DataBase.Create_Team import TeamCreator
from DataBase.Invite_team import TeamInvite
import sys
import os

from DataBase.user_db import UserDB

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from RAG.LLM.chat_system import ChatSystem
from RAG.load import Load

app = Flask(__name__)

# 챗시스템 객체 생성
chat_systems = {}

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
    name = request.form["client_name"]  # 이름 추가
    old = request.form["client_old"]  # 나이 추가
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


# 중복 확인
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


# 질의응답 페이지 보여주기
@app.route("/qa", methods=["GET"])
def qa_page():
    user_id = session.get("user_id")
    question = request.args.get("question", "")
    mode = request.args.get("mode", "personal")
    team_id = request.args.get("team_id")

    if not user_id:
        flash("로그인이 필요합니다.")
        return redirect(url_for("login"))

    team_creator = TeamCreator()
    user_teams = team_creator.get_user_teams(user_id)

    # 프롬프트 가져오기
    prompt_db = UserPrompt()
    user_prompts = prompt_db.getPrompt(user_id) or []

    # 팀 모드 처리: team_id 유효성 확인
    if mode == "team" and team_id:
        try:
            team_id = int(team_id)
        except ValueError:
            return "잘못된 팀 ID입니다.", 400

        if not any(team["Team_ID"] == team_id for team in user_teams):
            return "권한이 없는 팀입니다.", 403
    else:
        team_id = None  # 개인 모드일 때는 team_id 없음

    return render_template(
        "qa.html",
        question=question,
        mode=mode,
        team_id=team_id,
        teams=user_teams,  # 팀 목록 전달
        prompts=user_prompts, #프롬프트 전달
    )


# 질의응답
@app.route("/stream-ask", methods=["POST"])
def stream_ask():
    data = request.get_json()

    question = data.get("question", "").strip()

    user_id = session.get("user_id")

    mode = data.get("mode", "personal")

    team_id = data.get("team_id")
    print(f"team_id = {team_id}")
    
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

    if team_id:
        key = f"{user_id}_{team_id}"
    else:
        key = user_id

    if key not in chat_systems:
        chat_systems[key] = ChatSystem(user_id=user_id, team_id=team_id)

    chat_system = chat_systems[key]

    return Response(
        stream_with_context(chat_system.run(question)), content_type="text/plain"
    )


prompt_list = []


@app.route("/export_qna_json")
def export_qna_json():
    try:
        user_id = session.get("user_id")
        team_id = request.args.get("team_id", None)  # GET 파라미터에서 team_id를 받음
        if team_id:
            team_id = int(team_id)  # 문자열 -> 정수

        if not user_id:
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))

        print(f"user_id: {user_id}, team_id: {team_id}")

        exporter = TeamQnaExporter(user_id, team_id)
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
    if "user_id" not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    team_creator = TeamCreator()
    team_list = team_creator.get_my_created_teams(
        user_id
    )  # 내가 만든 팀 목록만 불러오기

    if request.method == "POST":
        team_id = request.form["team"]
        invited_user_id = request.form["user_id"]  # 이메일 대신 사용자 ID 입력 받기
        role = request.form["role"]

        # 초대처리
        team_invite = TeamInvite()

        success = team_invite.invite_member(team_id, invited_user_id, role)

        if success:
            flash(f"{invited_user_id} 님을 팀에 초대했습니다.")
        else:
            flash("초대 처리 중 오류가 발생했습니다.")

        return redirect(url_for("invite_member"))

    return render_template("invite_member.html", team_list=team_list)


# 가격 페이지
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

    user_id = session["user_id"]

    db = UserDB()
    user = db.get_user_info(session["user_id"])

    # 팀 정보 가져오기
    team_invite = TeamInvite()
    invited_teams = list(team_invite.get_user_teams(user_id))  # 리스트로 변환

    team_creator = TeamCreator()
    created_teams = list(team_creator.get_my_created_teams(user_id))  # 생성한 팀

    # 생성한 팀 데이터를 초대받은 팀과 형식 맞추기
    for team in created_teams:
        team["Role"] = "생성자"

    # 합치기
    teams = invited_teams + created_teams

    # 'Team_Name'이 존재하는 팀만 필터링
    teams = [team for team in teams if team.get("Team_Name")]

    # 팀별 팀원 정보 가져오기
    team_members = {}
    for team in teams:
        team_id = team["Team_ID"]
        team_members[team_id] = team_invite.get_team_members(team_id)

    return render_template(
        "mypage.html", user=user, teams=teams, team_members=team_members
    )


# 마이페이지 - 팀나가기
@app.route("/leave_team", methods=["POST"])
def leave_team():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    team_id = request.form["team_id"]

    team_invite = TeamInvite()
    success = team_invite.leave_team(user_id, team_id)

    if success:
        flash("팀에서 나갔습니다.")
    else:
        flash("팀 나가기 중 오류가 발생했습니다.")

    return redirect(url_for("mypage"))


# 마이페이지 - 팀삭제
@app.route("/delete_team", methods=["POST"])
def delete_team():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    team_id = request.form["team_id"]

    team_creator = TeamCreator()
    success = team_creator.delete_team(team_id, user_id)

    if success:
        flash("팀이 성공적으로 삭제되었습니다.")
    else:
        flash("팀 삭제 중 오류가 발생했습니다. (생성자만 삭제 가능)")

    return redirect(url_for("mypage"))

#요금제 저장
@app.route("/select_plan", methods=["POST"])
def select_plan():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    data = request.get_json()
    plan = data.get("plan")

    if not plan:
        return jsonify({"success": False, "message": "요금제 정보가 없습니다."}), 400

    user_id = session["user_id"]

    # DB에 요금제 저장
    db = UserDB()
    success = db.update_user_plan(user_id, plan)

    if success:
        session["plan"] = plan  # 선택 사항: 세션에 저장 (임시 캐시)
        return jsonify({"success": True, "message": "요금제가 저장되었습니다."})
    else:
        return jsonify({"success": False, "message": "DB 저장 실패"}), 500

#질의응답 페이지 - 프롬프트 선택 시 서버 처리
@app.route("/select_prompt", methods=["POST"])
def select_prompt():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    data = request.get_json()
    title = data.get("title")
    category = data.get("category")
    content = data.get("content")

    # 로그 확인용 - ChatSystem 연동 전
    print(f"프롬프트 선택됨: title={title}, category={category}, content={content}")

    #ChatSystem에 전달 로직 작성 해야 함
    return jsonify({"success": True, "message": "프롬프트 선택 성공"})

#질의응답 페이지- 프롬프트 수정
@app.route("/edit_prompt", methods=["GET", "POST"])
def edit_prompt():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    prompt_db = UserPrompt()

    if request.method == "POST":
        original_title = request.form["original_title"]
        new_title = request.form["title"]
        category = request.form["category"]
        content = request.form["content"]

        success = prompt_db.updatePrompt(user_id, original_title, new_title, category, content)
        if success:
            flash("프롬프트가 성공적으로 수정되었습니다.")
        else:
            flash("프롬프트 수정 중 오류가 발생했습니다.")
        return redirect(url_for("qa_page"))

    # GET 요청 → 수정 폼 로드
    title = request.args.get("title")
    prompt = prompt_db.getPromptByTitle(user_id, title)
    if not prompt:
        flash("프롬프트를 찾을 수 없습니다.")
        return redirect(url_for("qa_page"))

    return render_template("edit_prompt.html", prompt=prompt)

#질의응답 페이지 - 프롬프트 삭제
@app.route("/delete_prompt", methods=["POST"])
def delete_prompt():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    title = request.form["title"]

    prompt_db = UserPrompt()
    success = prompt_db.deletePrompt(user_id, title)

    if success:
        flash("프롬프트가 삭제되었습니다.")
    else:
        flash("프롬프트 삭제 중 오류가 발생했습니다.")

    return redirect(url_for("qa_page"))



# 서버 실행
if __name__ == "__main__":

    app.run(port=5901)
