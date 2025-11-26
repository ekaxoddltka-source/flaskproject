import pymysql

def get_db_connection():
    return pymysql.connect(
        host='192.168.60.187',
        user='jwh',
        password='ezen',
        db='aezen',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )