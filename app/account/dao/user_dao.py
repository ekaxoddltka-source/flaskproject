# app/account/dao/user_dao.py
import pymysql
from flask import current_app

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
                data["password"],  # 비밀번호 그대로 저장
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

    @staticmethod
    def get_user_by_name_email(name, email):
        db = current_app.get_db_connection()
        sql = "SELECT id FROM user WHERE name=%s AND email=%s AND withdraw=0"
        with db.cursor() as cursor:
            cursor.execute(sql, (name, email))
            result = cursor.fetchone()
        db.close()
        return result

    @staticmethod
    def get_user_by_all(userid, name, email):
        db = current_app.get_db_connection()
        sql = "SELECT id FROM user WHERE id=%s AND name=%s AND email=%s AND withdraw=0"
        with db.cursor() as cursor:
            cursor.execute(sql, (userid, name, email))
            result = cursor.fetchone()
        db.close()
        return result

    @staticmethod
    def update_password(userid, password):
        """임시 비밀번호 그대로 DB에 저장"""
        db = current_app.get_db_connection()
        sql = "UPDATE user SET password=%s WHERE id=%s"
        with db.cursor() as cursor:
            cursor.execute(sql, (password, userid))
        db.commit()
        db.close()
