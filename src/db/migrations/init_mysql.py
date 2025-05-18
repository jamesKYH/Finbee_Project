import pandas as pd
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv('./data/cards.csv')


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
CREATE TABLE IF NOT EXISTS cards (
    card_id INT PRIMARY KEY,
    card_name VARCHAR(255),
    company VARCHAR(100),
    image_url TEXT,
    card_type VARCHAR(50)
)
""")

for _, row in df.iterrows():
    sql = "REPLACE INTO cards (card_id, card_name, company, image_url, card_type) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (int(row['card_id']), row['card_name'], row['company'], row['image_url'], row['card_type']))

conn.commit()
cursor.close()
conn.close()
