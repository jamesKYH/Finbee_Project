import pandas as pd
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv('./data/customers.csv')

conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT')),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE'),
    charset='utf8mb4'
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    seq INT PRIMARY KEY,
    name VARCHAR(255),
    age INT,
    gender VARCHAR(10),
    recommended_card_id INT
)
""")

for _, row in df.iterrows():
    sql = "REPLACE INTO customers (seq, name, age, gender, recommended_card_id) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (
        int(row['seq']),
        row['name'],
        int(row['age']),
        row['gender'],
        int(row['recommended_card_id'])
    ))

conn.commit()
cursor.close()
conn.close()

print("✅ 고객 정보가 MySQL에 저장되었습니다.")
