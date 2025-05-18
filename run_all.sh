#!/bin/bash

# 현재 디렉토리를 PYTHONPATH에 추가
export PYTHONPATH="$PYTHONPATH:$(pwd)"
echo "✅ PYTHONPATH 설정: $PYTHONPATH"

echo "✅ 1. 패키지 설치"
pip install -r requirements.txt

echo "✅ 2. MySQL에 카드 정보 저장"
python3 src/db/migrations/init_mysql.py

echo "✅ 3. 혜택 설명 임베딩 및 ChromaDB 저장"
python3 src/models/insert_embeddings.py

echo "✅ 4. 고객 정보 MySQL에 저장"
python3 src/db/migrations/init_customers.py

echo "✅ 5. 추천 카드 정보 MySQL에 저장"
python3 src/db/migrations/init_recommended_cards.py

echo "🎉 모든 작업이 완료되었습니다!"

echo "✅ 6. 애플리케이션 실행"
streamlit run src/app.py
