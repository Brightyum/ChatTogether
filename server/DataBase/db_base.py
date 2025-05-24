import pymysql
import os
from dotenv import load_dotenv

# env파일에서 민감한 정보를 저장하고 os.getenv()로 호출
load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_user = os.getenv("DB_USER")
db_pwd = os.getenv("DB_PWD")

# db객체 설정
db = pymysql.connect(
    host=db_host,  # 호스트 ip(외부 데이터베이스 서버 ip)
    port=int(db_port),  # 데이터베이스 외부 포트
    user=db_user,  # 데이터베이스 사용자 이름
    password=db_pwd,  # 데이터베이스 사용자 비밀번호
    db="test",  # 데이터베이스 테이블 이름
    charset="utf8",  # 한국어 안깨지도록 설정
)

# 데이터 접근 설정
cursor = db.cursor()

# 쿼리문
# #클라이언트 테이블(가장 기초적인 테이블) 
# Client_Table = "create table Client_Table(Client_ID char(8) primary key not null, Client_Pass char(8) not null, Client_Sch char(8) not null, Client_API varchar(60) not null, Client_Eml varchar(45) not null, Client_Num int, Client_Per char(8)not null, Client_Gen enum('male','female')not null)"
# # 개인 테이블 (개인 질의 응답 및 개인 아이디와 대화의 주제 중점을 저장하는 테이블)
# Personal_Table = "create table Personal_Table(Personal_ID char(8) primary key not null, Personal_qna varchar(1000) not null, personal_rep varchar(1000) not null, Personal_Type char(10) not null, Constraint gain_inform foreign key(Personal_ID) references Client_table(Client_ID) )"
# #팀 테이블1 (팀원들의 아이디와 각각의 역할을 저장하는 테이블)
# Team_Table = "create table Team_Table(Team_ID char(20)primary key not null, ClientID_fir char(8) not null, ClientID_sec char(8) not null, ClientID_thr char(8) not null, ClientID_fou char(8) not null, ClientID_fiv char(8) not null, ClientID_six char(8) not null, ClientType_fir char(8) not null, ClientType_sec char(8) not null, ClientType_thr char(8) not null, ClientType_fou char(8) not null, ClientType_fiv char(8) not null, ClientType_six char(8) not null, Constraint fir_gain foreign key(ClientID_fir) references Client_table(Client_ID), Constraint sec_gain foreign key(ClientID_sec) references Client_table(Client_ID), Constraint thr_gain foreign key(ClientID_thr) references Client_table(Client_ID), Constraint fou_gain foreign key(ClientID_fou) references Client_table(Client_ID), Constraint fiv_gain foreign key(ClientID_fiv) references Client_table(Client_ID), Constraint six_gain foreign key(ClientID_six) references Client_table(Client_ID))"
# # 팀 테이블2 (팀기능으로 사용할때 발생하는 질의 응답과 그것의 아이디와 시간을 저장하는 테이블)
# Team_Qna_Table = "create table Team_Qna_Table(qna_id int not null, team_id char(20) primary key,team_que longtext, team_asw longtext, date datetime, constraint Team_exchange foreign key(team_id) references Team_Table(Team_ID))"
# # 쿼리문 데이터베이스에 실행
# cursor.execute(Client_Table)
# cursor.execute(Personal_Table)
# cursor.execute(Team_Table)
# cursor.execute(Team_Qna_Table)
Client_Table="select*from Client_Table"
inser="insert into Client_Table values('abs8027','@msh0206','동의대학교','API키','abs8027@gmail_com','01012341224','tableID','male')"

cursor.execute(Client_Table)



result = cursor.fetchall()  # 모든 행 가져오기
# cursor.fetchone() # 하나의 행만 가져오기
# cursor.fetchmany(n) # n개의 데이터 가져오기

print(result)

db.commit()  # 데이터베이스에 생성,삭제,수정 등 데이터 변동이 생기면 commit()으로 저장을 해줘야함
db.close()  # 데이터베이스 사용후에는 close()로 객체를 닫아줘야함
