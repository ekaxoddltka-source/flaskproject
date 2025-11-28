# app/account/dao/user_dao.py

import pymysql
from datetime import datetime
# 중요: get_db_connection 함수는 app/account/routes.py에 정의되어 있으므로 상대 경로로 import 합니다.
# 실제 프로젝트 구조에 따라 경로는 달라질 수 있습니다.
from flask import current_app

class UserDao:
    """
    User Data Access Object (사용자 데이터베이스 접근 객체)

    담당 기능:
    1. 아이디 중복 확인 (check_id_duplicate)
    2. 신규 사용자 정보 삽입 (insert_user)
    """

    def check_id_duplicate(self, user_id):
        """
        아이디 중복 여부를 확인합니다.
        
        :param user_id: 사용자가 입력한 아이디 (문자열)
        :return: True (중복), False (사용 가능)
        """
        conn = current_app.get_db_connection()
        # count 쿼리이므로 DictCursor 대신 일반 Cursor를 사용하는 것이 효율적일 수 있습니다.
        cursor = conn.cursor() 
        
        sql = "SELECT COUNT(*) FROM user WHERE id = %s"
        try:
            # 쿼리 실행
            cursor.execute(sql, (user_id,))
            
            # 결과 가져오기 (튜플 형태로 반환됨, 예: (1,) 또는 (0,))
            count = cursor.fetchone()[0] 
            
            # 1개 이상이면 중복 (True 반환)
            return count > 0 
        except Exception as e:
            # 데이터베이스 연결 또는 쿼리 오류 발생 시
            print(f"Error checking ID duplicate: {e}")
            # 안전하게 중복으로 처리하여 가입을 막거나, 서버 오류로 처리할 수 있습니다.
            return True # 오류 시 안전을 위해 True 반환
        finally:
            cursor.close()
            conn.close()

    def insert_user(self, data):
        """
        새로운 사용자 정보를 user 테이블에 삽입합니다.
        
        :param data: 회원가입 정보 딕셔너리. (필수: 'id', 'password', 'email', 'nickname')
        :return: True (삽입 성공), False (삽입 실패)
        """
        conn = current_app.get_db_connection()
        cursor = conn.cursor()
        
        # SQL 쿼리 정의 (DB 테이블 컬럼명에 맞춰 작성)
        sql = """
        INSERT INTO user (
            id, password, email, nickname, 
            reg_date, last_login_at, withdraw, 
            marketing_agree_status  -- 마케팅 동의 상태를 저장할 컬럼 (추가 가정)
        ) VALUES (
            %s, %s, %s, %s, 
            %s, %s, %s, 
            %s
        )
        """
        
        # 파라미터 튜플 생성
        params = (
            data['id'],
            data['password'], 
            data['email'],
            data.get('nickname', data['id']), # 닉네임이 없으면 ID를 기본값으로 사용
            datetime.now(),
            datetime.now(),
            0, # withdraw: 0 = 정상 회원
            data.get('agree-marketing', 'off') # 마케팅 동의 정보
        )
        
        try:
            # 쿼리 실행
            cursor.execute(sql, params)
            conn.commit() # 데이터베이스 변경 사항 확정
            return True
        except pymysql.err.IntegrityError as e:
            # DB 무결성 오류 (예: UNIQUE 제약 조건 위반, NOT NULL 위반 등)
            print(f"Integrity Error during user insert: {e}")
            conn.rollback()
            return False
        except Exception as e:
            # 기타 오류
            print(f"UserDao insert_user Error: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

#