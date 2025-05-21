import pymysql
import os
from dotenv import load_dotenv


# 데이터베이스 초기 환경설정 클래스
# 객체 생성후 getDb로 불러서 사용
class Db:

    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_pwd = os.getenv("DB_PWD")
        self.db = None

    def setDb(self):
        self.db = pymysql.connect(
            host=self.db_host,  # 호스트 ip(외부 데이터베이스 서버 ip)
            port=int(self.db_port),  # 데이터베이스 외부 포트
            user=self.db_user,  # 데이터베이스 사용자 이름
            password=self.db_pwd,  # 데이터베이스 사용자 비밀번호
            db="test",  # 데이터베이스 테이블 이름
            charset="utf8",  # 한국어 안깨지도록 설정
        )

    def getDb(self):
        if self.db is None:
            self.setDb()
        return self.db
