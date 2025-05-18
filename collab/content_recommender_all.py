import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

# Step-by-step instructions:
# 1. Delete or rename the existing `./chroma_db` directory
# 2. Re-run this script to re-insert all embeddings
# 3. Re-run `content_recommender.py` to apply updated content-based recommendations

chroma_client = chromadb.PersistentClient(path="./chroma_db")

model = SentenceTransformer('all-MiniLM-L6-v2')

df = pd.read_csv('../data/benefits.csv')

collection = chroma_client.get_or_create_collection(name="card_benefits")

total_rows = len(df)
progress_step = max(1, total_rows // 20)

for i, row in df.iterrows():
    if pd.isna(row['card_id']) or pd.isna(row['benefit_text']):
        continue  # skip invalid rows
    if i % progress_step == 0:
        print(f"진행 중: {i}/{total_rows}개 문서 임베딩 중... ({i/total_rows*100:.1f}%)")
    embedding = model.encode(row['benefit_text']).tolist()
    collection.add(
        documents=[row['benefit_text']],
        embeddings=[embedding],
        metadatas=[{
            "card_id": int(row['card_id']),
            "card_name": str(row['card_name']) if not pd.isna(row.get('card_name', None)) else ""
        }],
        ids=[f"benefit_{i}"]
    )

# chroma_client.persist()

import os
import pymysql
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("card_benefits")

model = SentenceTransformer('all-MiniLM-L6-v2')

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    charset="utf8mb4"
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS content_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seq VARCHAR(50),
    recommended_card_id INT,
    card_name VARCHAR(255),
    score FLOAT
)
""")

cursor.execute("SELECT DISTINCT seq FROM recommended_cards")
all_seqs = [row[0] for row in cursor.fetchall()][:50]

card_df = pd.read_sql("SELECT card_id, card_name FROM cards", conn)
card_dict = dict(zip(card_df.card_id, card_df.card_name))

insert_batch = []

for seq in all_seqs:
    cursor.execute("SELECT DISTINCT id FROM recommended_cards WHERE seq = %s", (seq,))
    user_card_ids = [int(row[0]) for row in cursor.fetchall()]
    if not user_card_ids:
        continue

    result = collection.get(where={"card_id": {"$in": user_card_ids}})
    vectors = result.get("embeddings") or []
    if not vectors:
        continue

    query_vector = np.mean(np.array(vectors), axis=0).tolist()
    similar = collection.query(query_embeddings=[query_vector], n_results=10)

    metadatas = similar["metadatas"][0]
    scores = similar["distances"][0]

    added = 0
    for meta, score in zip(metadatas, scores):
        card_id = int(meta["card_id"])
        if card_id in user_card_ids:
            continue
        card_name = card_dict.get(card_id, "")
        insert_batch.append((seq, card_id, card_name, score))
        added += 1
        if added == 3:
            break

if insert_batch:
    cursor.executemany(
        "INSERT INTO content_recommendations (seq, recommended_card_id, card_name, score) VALUES (%s, %s, %s, %s)",
        insert_batch
    )
    conn.commit()

cursor.close()
conn.close()
print("✅ 콘텐츠 기반 추천 완료")
