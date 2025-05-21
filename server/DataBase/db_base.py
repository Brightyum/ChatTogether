import pymysql
import os
from dotenv import load_dotenv

# env파일에서 민감한 정보를 저장하고 os.getenv()로 호출
# load_dotenv()
# db_host = os.getenv("DB_HOST")
# db_port = os.getenv("DB_PORT")
# db_user = os.getenv("DB_USER")
# db_pwd = os.getenv("DB_PWD")

# db객체 설정
# db = pymysql.connect(
#     host=db_host,  # 호스트 ip(외부 데이터베이스 서버 ip)
#     port=int(db_port),  # 데이터베이스 외부 포트
#     user=db_user,  # 데이터베이스 사용자 이름
#     password=db_pwd,  # 데이터베이스 사용자 비밀번호
#     db="test",  # 데이터베이스 테이블 이름
#     charset="utf8",  # 한국어 안깨지도록 설정
# )

# # 데이터 접근 설정
# cursor = db.cursor()

# # 쿼리문
# sql = "SELECT * FROM testTable"
# # 쿼리문 데이터베이스에 실행
# cursor.execute(sql)

# result = cursor.fetchall()  # 모든 행 가져오기
# # cursor.fetchone() # 하나의 행만 가져오기
# # cursor.fetchmany(n) # n개의 데이터 가져오기

# print(result)

# db.commit()  # 데이터베이스에 생성,삭제,수정 등 데이터 변동이 생기면 commit()으로 저장을 해줘야함
# db.close()  # 데이터베이스 사용후에는 close()로 객체를 닫아줘야함

load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")  
db_user = os.getenv("DB_USER")
db_pwd = os.getenv("DB_PWD")
db_name = os.getenv("DB_NAME")

#  데이터베이스 연결 객체를 반환하는 함수
def get_connection():
    return pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_pwd,
        db=db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor  # 결과를 딕셔너리로 받기 위함
    )

def test_select_all():
    conn = get_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM testTable"
    cursor.execute(sql)

    result = cursor.fetchall()
    print(result)

    conn.commit()
    conn.close()


