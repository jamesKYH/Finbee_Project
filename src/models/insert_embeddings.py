import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
import os

# ChromaDB 경로 후보들
chroma_paths = [
    "./db_backup/chroma_db",
    "../db_backup/chroma_db",
    "/Users/james_kyh/Downloads/card_rag_project_collab_all_users 4/db_backup/chroma_db"
]

# 적절한 ChromaDB 경로 찾기
chroma_client = None
for path in chroma_paths:
    try:
        print(f"ChromaDB 경로 시도: {path}")
        chroma_client = chromadb.PersistentClient(path=path)
        # 간단한 작업으로 연결 테스트
        try:
            chroma_client.list_collections()
            print(f"✅ ChromaDB 연결 성공: {path}")
            break
        except:
            raise Exception("연결 테스트 실패")
    except Exception as e:
        print(f"❌ ChromaDB 연결 실패: {path}, 오류: {str(e)}")
        continue

if chroma_client is None:
    raise Exception("ChromaDB에 연결할 수 없습니다. 경로를 확인해주세요.")

# Sentence-BERT 모델 로드
model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')

# 현재 파일 경로에서 데이터 파일 경로 추정
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
benefits_csv_path = os.path.join(current_dir, 'data', 'benefits.csv')

print(f"데이터 파일 로드 중: {benefits_csv_path}")
df = pd.read_csv(benefits_csv_path)

# 기존 컬렉션이 있으면 삭제
try:
    chroma_client.delete_collection(name="card_benefits")
    print("기존 card_benefits 컬렉션 삭제 완료")
except:
    print("기존 컬렉션이 없거나 삭제할 수 없습니다.")

# 새 컬렉션 생성
collection = chroma_client.create_collection(name="card_benefits")
print("새 card_benefits 컬렉션 생성 완료")

# card_id별로 benefit_text 모으기
grouped = df.dropna(subset=['card_id', 'benefit_text']).groupby('card_id')['benefit_text'].apply(list).reset_index()

total_rows = len(grouped)
progress_step = max(1, total_rows // 20)

for i, row in grouped.iterrows():
    if i % progress_step == 0:
        print(f"진행 중: {i}/{total_rows}개 카드 임베딩 중... ({i/total_rows*100:.1f}%)")

    benefit_list = row['benefit_text']

    # 의미 없는 문구를 제거하는 필터링
    cleaned_benefits = []
    for benefit in benefit_list:
        if any(skip in benefit for skip in ["확인", "변동될 수 있습니다", "주의사항", "유의사항"]):
            continue
        cleaned_benefits.append(benefit)

    if not cleaned_benefits:
        continue  # 모든 혜택이 무의미한 문장이면 저장하지 않음

    merged_text = "\n".join(f"- {benefit}" for benefit in cleaned_benefits)  # 필터링된 혜택만 합치기

    embedding = model.encode(merged_text).tolist()

    # 디버깅 출력 (처음 10개만)
    if i < 10:
        print(f"{i+1}: 카드 ID = {row['card_id']} - 혜택 {len(cleaned_benefits)}개 합침")

    # 카드 ID 메타데이터로 저장
    collection.add(
        documents=[merged_text],
        embeddings=[embedding],
        metadatas=[{
            "card_id": int(row['card_id'])
        }],
        ids=[f"benefit_{row['card_id']}"]
    )
