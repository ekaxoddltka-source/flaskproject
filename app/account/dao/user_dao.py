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

            # 2. 관심분야 insert
            if interests:
                sql_interest = "INSERT INTO user_interests (user_id, interest) VALUES (%s, %s)"
                for item in interests:
                    cursor.execute(sql_interest, (data["id"], item))

            # 3. 기술 insert
            if skills:
                sql_skill = "INSERT INTO user_skills (user_id, skill) VALUES (%s, %s)"
                for item in skills:
                    cursor.execute(sql_skill, (data["id"], item))

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
