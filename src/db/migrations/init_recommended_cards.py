import pandas as pd
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv('./data/card_assignment_result_final.csv')

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
CREATE TABLE IF NOT EXISTS recommended_cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seq VARCHAR(50),
    cluster INT,
    recommended_rank INT,
    card_code VARCHAR(10),
    card_id INT,
    card_name VARCHAR(255)
)
""")

cursor.execute("DELETE FROM recommended_cards")

card_df = pd.read_sql("SELECT card_id, card_name FROM cards", conn)
card_dict = dict(zip(card_df.card_id, card_df.card_name))

def parse_card_code(card_code):
    if card_code.startswith("C"):
        return "체크카드", int(card_code[1:])
    elif card_code.startswith("R"):
        return "신용카드", int(card_code[1:]) + 1000
    return None, None

insert_batch = []
total_rows = len(df)
progress_step = max(1, total_rows // 20)

for idx, (_, row) in enumerate(df.iterrows()):
    seq = str(row['SEQ'])
    cluster = int(row['cluster'])
    for i in range(1, 8):
        col = f'card_{i}'
        if pd.notna(row[col]):
            card_code = str(row[col])
            card_type, card_id = parse_card_code(card_code)
            card_name = card_dict.get(card_id)
            insert_batch.append((seq, cluster, i, card_code, card_id, card_name))
    
    # 매 1000개마다 일괄 삽입
    if len(insert_batch) >= 1000:
        cursor.executemany(
            "INSERT INTO recommended_cards (seq, cluster, recommended_rank, card_code, card_id, card_name) VALUES (%s, %s, %s, %s, %s, %s)",
            insert_batch
        )
        conn.commit()
        print(f"[진행 상황] {idx+1}/{total_rows}행 처리됨 ({(idx+1)/total_rows*100:.1f}%)")
        insert_batch = []

# 남은 데이터 일괄 삽입
if insert_batch:
    cursor.executemany(
        "INSERT INTO recommended_cards (seq, cluster, recommended_rank, card_code, card_id, card_name) VALUES (%s, %s, %s, %s, %s, %s)",
        insert_batch
    )
    conn.commit()
    print(f"[진행 상황] 전체 {total_rows}행 처리 완료")

cursor.close()
conn.close()

print("✅ 추천 카드 정보가 MySQL에 저장되었습니다.")
