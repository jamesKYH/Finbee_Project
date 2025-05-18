# 📁 db/utils.py

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ 사용자 정보 가져오기 (DictCursor 적용)
def get_user_profile(user_id: str):
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset='utf8mb4'
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✨ DictCursor로 변경
    cursor.execute("SELECT * FROM user_transactions WHERE SEQ = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result  # ✨ Dict로 바로 나오니까 zip() 불필요

# ✅ 추천 카드 가져오기 (새로 추가)
def get_recommended_cards(user_id: str):
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT card_name FROM user_recommendations_hybrid WHERE user_id = %s", (user_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return [row[0] for row in results] if results else []