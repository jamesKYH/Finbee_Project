import os
import pymysql
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI
from typing import List, Tuple

# ✅ 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ MySQL 연결
conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    charset="utf8mb4"
)

# ✅ ChromaDB 클라이언트 초기화 (여러 경로 시도)
chroma_client = None
collection = None

# ChromaDB 경로 후보들
chroma_paths = [
    "./db_backup/chroma_db",
    "../db_backup/chroma_db",
    "/Users/james_kyh/Downloads/card_rag_project_collab_all_users 4/db_backup/chroma_db"
]

for path in chroma_paths:
    try:
        print("ChromaDB 경로 시도: {}".format(path))
        client = chromadb.PersistentClient(path=path)
        collection = client.get_collection("card_benefits")
        print("✅ ChromaDB 연결 성공: {}".format(path))
        break
    except Exception as e:
        print("❌ ChromaDB 연결 실패: {}, 오류: {}".format(path, str(e)))
        continue

if collection is None:
    print("⚠️ 경고: ChromaDB 컬렉션을 찾을 수 없습니다. 먼저 insert_embeddings.py를 실행해주세요.")

# ✅ Sentence-BERT 임베딩 모델 로드
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")

# ✅ OpenAI 클라이언트 준비
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ 사용자 정보 요약 함수
def get_user_profile_summary(user_id: str) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_transactions WHERE SEQ = %s", (user_id,))
    result = cursor.fetchone()
    columns = [col[0] for col in cursor.description]
    cursor.close()

    if result:
        user = dict(zip(columns, result))
        
        # 소비 항목 관련 컬럼들 추출
        spending_columns = [col for col in user.keys() if col.endswith('_mean') and not col.startswith('TOT_')]
        
        # 소비 금액이 높은 순으로 정렬 (상위 8개만)
        top_spending = sorted(
            [(col.replace('_AM_mean', ''), user.get(col, 0)) for col in spending_columns],
            key=lambda x: x[1], 
            reverse=True
        )[:8]
        
        # 소비 카테고리 매핑
        category_mapping = {
            "CLOTH": "쇼핑/의류",
            "RESTRNT": "외식",
            "TRVL": "여행",
            "INSU": "보험",
            "HOS": "의료/병원",
            "CULTURE": "문화생활",
            "OFFEDU": "교육",
            "LEISURE_P": "레저/취미",
            "LEISURE_S": "스포츠",
            "DIST": "유통",
            "GROCERY": "식료품",
            "AUTOSL": "자동차",
            "FUNITR": "가구/인테리어",
            "APPLNC": "가전제품"
        }
        
        summary_lines = [
            "[사용자 정보 요약]",
            f"- 연령대: {user['AGE_encoded']}0대",
            f"- 성별: {'여성' if user['SEX_CD_encoded'] == 1 else '남성'}",
            f"- 디지털 채널 이용: {'예' if user['DIGT_CHNL_USE_YN_encoded'] == 1 else '아니오'}",
            "- 최근 소비 항목 분석 (월평균 지출):"
        ]
        
        # 상위 소비 항목 추가
        for category, amount in top_spending:
            if amount > 0:
                category_name = category_mapping.get(category, category)
                summary_lines.append(f"  • {category_name}: {amount*1000:,.0f}원")
        
        # 주요 소비 패턴 분석
        if user.get('TOP_SPENDING_CATEGORY_encoded'):
            summary_lines.append("")
            summary_lines.append("[주요 소비 패턴]")
            summary_lines.append(f"- 최대 지출 카테고리: {category_mapping.get(user.get('TOP_SPENDING_CATEGORY_encoded'), user.get('TOP_SPENDING_CATEGORY_encoded'))}")
            
            # 소비 성향 분석
            total_spending = user.get('TOT_USE_AM_mean', 0)
            if total_spending > 0:
                # 소비 집중도 분석
                if top_spending and top_spending[0][1] > total_spending * 0.3:
                    summary_lines.append(f"- 소비 성향: 특정 카테고리({category_mapping.get(top_spending[0][0], top_spending[0][0])})에 집중된 소비 패턴")
                else:
                    summary_lines.append(f"- 소비 성향: 다양한 카테고리에 분산된 소비 패턴")
                
                # 소비 규모 분석
                if total_spending > 2.0:  # 200만원 이상
                    summary_lines.append(f"- 소비 규모: 고액 소비자 (월평균 {total_spending*1000:,.0f}원)")
                elif total_spending > 1.0:  # 100만원 이상
                    summary_lines.append(f"- 소비 규모: 중간 소비자 (월평균 {total_spending*1000:,.0f}원)")
                else:
                    summary_lines.append(f"- 소비 규모: 소액 소비자 (월평균 {total_spending*1000:,.0f}원)")
                
                # 소비 패턴 분석
                leisure_spending = sum([amount for category, amount in top_spending if category in ["TRVL", "CULTURE", "LEISURE_P", "LEISURE_S"]])
                daily_spending = sum([amount for category, amount in top_spending if category in ["RESTRNT", "GROCERY", "DIST"]])
                
                if leisure_spending > daily_spending * 1.5:
                    summary_lines.append(f"- 소비 특성: 여가/문화 활동 중심 소비자")
                elif daily_spending > leisure_spending * 1.5:
                    summary_lines.append(f"- 소비 특성: 일상/생활 중심 소비자")
                else:
                    summary_lines.append(f"- 소비 특성: 균형 있는 소비자")

        return "\n".join(summary_lines)
    return ""

# ✅ 메인 함수: 개인화된 카드 추천 RAG
def ask_card_rag(question, user_id=None, chat_history=None, top_k=5, stream=False) -> Tuple[str, List[dict], List[str]]:
    cursor = conn.cursor()

    # 1. 질문 임베딩 생성
    query_vec = model.encode(question).tolist()

    # 2. ChromaDB에서 embedding similarity 기반 검색
    try:
        # 최신 버전의 ChromaDB는 include_distances 파라미터를 지원
        results = collection.query(query_embeddings=[query_vec], n_results=top_k, include_distances=True)
    except TypeError:
        # 이전 버전의 ChromaDB는 include_distances 파라미터를 지원하지 않음
        results = collection.query(query_embeddings=[query_vec], n_results=top_k)

    # 3. 검색 결과 확인
    benefit_docs = results['documents'][0] if results['documents'] else []
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    
    # 거리 정보가 없으면 모든 결과에 순서에 따른 유사도 할당
    if 'distances' in results and results['distances']:
        distances = results['distances'][0]
    else:
        # 거리 정보가 없는 경우 순서에 따라 유사도 점수 할당 (첫 번째 결과가 가장 유사)
        distances = [(idx * 0.1) for idx in range(len(benefit_docs))]

    if not benefit_docs:
        cursor.close()
        return "죄송합니다. 해당 혜택과 관련된 카드를 찾지 못했습니다. 😥", [], []

    # 4. 카드 ID로 정형 정보 조회
    card_ids = [meta['card_id'] for meta in metadatas]
    card_info_dict = {}
    if card_ids:
        placeholders = ','.join(['%s'] * len(card_ids))
        cursor.execute(
            f"SELECT card_id, card_name, company, image_url, card_type FROM cards WHERE card_id IN ({placeholders})",
            tuple(card_ids)
        )
        for row in cursor.fetchall():
            card_info_dict[row[0]] = {
                "card_name": row[1],
                "company": row[2],
                "image_url": row[3],
                "card_type": row[4]
            }

    # 5. context 구성
    context_lines = []
    image_info = []
    
    # 유사도 점수를 기반으로 결과 정렬 (추가된 기능)
    result_items = []
    for idx, (meta, doc) in enumerate(zip(metadatas, benefit_docs)):
        # 거리 정보를 사용하여 유사도 계산 (거리가 작을수록 유사도가 높음)
        if idx < len(distances):
            # 거리를 0~1 사이의 유사도 점수로 변환 (1이 가장 유사)
            similarity = 1.0 - min(distances[idx], 1.0)
        else:
            # 거리 정보가 없는 경우 순서에 따라 유사도 할당
            similarity = 1.0 - (idx * 0.1)
        
        result_items.append((meta, doc, similarity, idx))
    
    # 유사도 점수 기준으로 내림차순 정렬
    result_items.sort(key=lambda x: x[2], reverse=True)
    
    for meta, doc, similarity, original_idx in result_items:
        card_id = meta['card_id']
        card_info = card_info_dict.get(card_id, {})
        card_name = card_info.get("card_name", "카드명 미상")
        company = card_info.get("company", "카드사 정보 없음")
        card_type = card_info.get("card_type", "")
        image_url = card_info.get("image_url", "")
        
        # 유사도 점수를 컨텍스트에 포함 (추가된 기능)
        context_lines.append(
            "[카드정보 #{0} (유사도: {1:.2f})]\n카드명: {2}\n카드사: {3}\n카드 유형: {4}\n혜택 설명: {5}\n카드 이미지: {6}".format(
                original_idx+1, similarity, card_name, company, card_type, doc, image_url
            )
        )
        image_info.append({
            "card_id": card_id,
            "card_name": card_name,
            "image_url": image_url,
            "similarity": similarity  # 유사도 점수도 저장 (추가된 기능)
        })
    context = "\n\n".join(context_lines)

    # 6. 유저 정보 프롬프트 요약
    user_summary = get_user_profile_summary(user_id) if user_id else ""

    # 7. 이전 대화 프롬프트 구성
    history_prompt = ""
    if chat_history:
        for i, (q, a) in enumerate(chat_history):
            history_prompt += "[이전 질문 {0}]: {1}\n[이전 답변 {2}]: {3}\n\n".format(i+1, q, i+1, a)

    # 8. 전체 프롬프트 구성
    messages = [
        {
            "role": "system",
            "content": """
너는 금융 카드 추천 전문가이자 카드 혜택 분석가야. 
고객의 소비 패턴과 요구사항을 분석하여 최적의 신용카드나 체크카드를 추천해줘야 해.

반드시 다음 원칙을 지켜야 해:
1. 제공된 카드 정보(context)에 포함된 내용만 사용할 것
2. 높은 유사도 점수를 가진 카드를 우선적으로 고려할 것
3. 혜택 설명은 context에 있는 내용을 그대로 사용할 것
4. 사용자의 소비 패턴과 가장 관련성 높은 카드를 우선 추천할 것
5. 각 카드의 핵심 혜택을 명확하게 강조할 것
6. 없는 정보는 절대 생성하지 말 것
7. 제공된 모든 카드에 대한 추천 정보를 빠짐없이 제공할 것
8. 답변은 항상 한국어로 작성할 것
9. 사용자의 소비 패턴을 고려하여 맞춤형 추천을 제공할 것
10. 유사도 점수가 높은 순서대로 카드를 정렬하여 제시할 것
11. 광고 문구나 마케팅 문구를 생성하지 말 것
12. 사용자의 질문에 직접적으로 답변하고, 불필요한 소개나 결론을 최소화할 것

답변은 항상 정확하고 간결하게 구성해야 합니다.
사용자에게 제공된 모든 카드 정보를 분석하고, 각 카드에 대한 설명을 제공해야 합니다.
절대로 카드 정보를 누락하지 마세요.
광고 문구나 마케팅 문구는 생성하지 마세요. 오직 객관적인 카드 정보와 혜택만 설명하세요.
"""
        },
        {
            "role": "user",
            "content": """
{0}

{1}

[사용자 질문]
{2}

[카드 정보 목록]
{3}

위 카드 정보 중에서 질문에 가장 적합한 카드들을 선택해서 추천해주세요. 
높은 유사도 점수를 가진 카드들을 우선적으로 고려하고, 
사용자의 소비 패턴과 관련성이 높은 카드를 우선 추천해주세요.

반드시 검색된 모든 카드({4}개)에 대해 추천 정보를 제공해야 합니다.
각 카드의 장단점을 명확히 설명하고, 어떤 상황에 적합한지 구체적으로 설명해주세요.

광고 문구나 마케팅 문구는 생성하지 마세요. 오직 객관적인 카드 정보와 혜택만 설명하세요.
불필요한 소개나 결론을 최소화하고, 사용자 질문에 직접적으로 답변하세요.

다음 형식으로 답변을 구성해주세요:
---
1. 카드명: [카드 이름]  
   - 카드사 및 유형: [카드사], [카드 유형]  
   - 관련 혜택: [context에 포함된 혜택 설명 그대로 작성]  
   - 추천 이유: [사용자 질문과 관련된 혜택을 간략히 설명]
2. ...
(모든 카드에 대해 위 형식으로 추천 정보 제공)
---
""".format(
                user_summary,
                '[이전 대화 기록]\n{}'.format(history_prompt) if chat_history else '',
                question,
                context,
                len(result_items)
            )
        }
    ]

    # 9. OpenAI 호출
    cursor.close()
    
    if stream:
        # 스트리밍 모드로 호출
        completion_stream = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            stream=True
        )
        return completion_stream, image_info, card_ids
    else:
        # 일반 모드로 호출
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        return completion.choices[0].message.content, image_info, card_ids

# ✅ 단독 실행용
if __name__ == "__main__":
    print("💬 궁금한 카드 혜택 질문을 입력하세요:")
    user_id = input("👤 사용자 ID: ")
    question = input("❓ 질문: ")
    answer, images, contexts = ask_card_rag(question, user_id=user_id)
    print("\n💡 RAG 기반 추천 결과:\n")
    print(answer)

    print("\n🖼️ 관련 카드 이미지 URL:")
    for item in images:
        print("{0}: {1}".format(item['card_name'], item['image_url']))