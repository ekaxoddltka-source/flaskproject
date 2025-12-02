# app/account/dao/user_dao.py
import pymysql
from flask import current_app
from werkzeug.security import generate_password_hash

class UserDao:
    """User Data Access Object"""

    def insert_user(self, data, interests=None, skills=None):
        """회원가입: 기본 유저 + 관심분야/기술 저장"""
        conn = current_app.get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. 기본 유저 정보 insert
            sql_user = """
            INSERT INTO user (
                id, password, name, nick, email, created_at, last_login_at, withdraw
            ) VALUES (
                %s, %s, %s, %s, %s, NOW(), NOW(), 0
            )
            """
            params_user = (
                data["id"],
                data["password"],
                data["name"],
                data["nick"],  # nickname은 nick 컬럼에 들어감
                data["email"]
            )
            cursor.execute(sql_user, params_user)

            # 2. user_attributes insert (관심분야 + 기술)
            sql_attr = "INSERT INTO user_attributes (user_id, type, value) VALUES (%s, %s, %s)"

            if interests:
                for item in interests:
                    cursor.execute(sql_attr, (data["id"], 'interest', item))

            if skills:
                for item in skills:
                    cursor.execute(sql_attr, (data["id"], 'skill', item))

            conn.commit()
            return True

        except Exception as e:
            import traceback
            print("UserDao insert_user Error:", e)
            traceback.print_exc()
            conn.rollback()
            return False

        finally:
            cursor.close()
            conn.close()
