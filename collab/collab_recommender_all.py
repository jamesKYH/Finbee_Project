import pymysql
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    charset="utf8mb4"
)
cursor = conn.cursor()

# 테이블 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS collab_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seq VARCHAR(50),
    recommended_card_code VARCHAR(10),
    score INT,
    source VARCHAR(20),
    card_name VARCHAR(255)
)
""")

# 모든 고객 seq 불러오기
cursor.execute("SELECT DISTINCT seq FROM recommended_cards")
all_seqs = [row[0] for row in cursor.fetchall()]

def parse_card_code(card_code):
    if card_code.startswith("C"):
        return int(card_code[1:])
    elif card_code.startswith("R"):
        return int(card_code[1:]) + 1000
    return None

for target_seq in all_seqs:
    cursor.execute("SELECT card_code FROM recommended_cards WHERE seq = %s", (target_seq,))
    my_cards = [row[0] for row in cursor.fetchall()]

    if not my_cards:
        continue

    placeholders = ', '.join(['%s'] * len(my_cards))
    cursor.execute(f"""
        SELECT DISTINCT seq FROM recommended_cards
        WHERE card_code IN ({placeholders}) AND seq != %s
    """, (*my_cards, target_seq))
    similar_users = [row[0] for row in cursor.fetchall()]

    if similar_users:
        placeholders = ', '.join(['%s'] * len(similar_users))
        cursor.execute(f"""
            SELECT card_code FROM recommended_cards
            WHERE seq IN ({placeholders})
        """, tuple(similar_users))
        other_cards = [row[0] for row in cursor.fetchall()]
    else:
        other_cards = []

    final_candidates = [card for card in other_cards if card not in my_cards]
    top_cards = Counter(final_candidates).most_common(3)

    cursor.execute("DELETE FROM collab_recommendations WHERE seq = %s", (target_seq,))
    for card, score in top_cards:
        card_id = parse_card_code(card)
        cursor.execute("SELECT card_name FROM cards WHERE card_id = %s", (card_id,))
        result = cursor.fetchone()
        card_name = result[0] if result else None

        cursor.execute(
            "INSERT INTO collab_recommendations (seq, recommended_card_code, score, source, card_name) VALUES (%s, %s, %s, %s, %s)",
            (target_seq, card, score, "collaborative", card_name)
        )

conn.commit()
cursor.close()
conn.close()
print("✅ 모든 고객 대상 협업 필터링 추천 완료")