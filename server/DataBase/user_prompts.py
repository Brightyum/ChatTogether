import pymysql
import os
from dotenv import load_dotenv
from db import Db

class UserPrompt():

    def __init__(self):
        self.db = Db().getDb()
    
    def savePrompt(self):
        
