# marketing_generator.py

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from openai import OpenAI

# 환경변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MySQL 연결
engine = create_engine(
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"
)

# 카드 정보 테이블 읽어오기
card_info_df = pd.read_sql("SELECT * FROM card_info", engine)

def summarize_card_benefits_openai(card_name: str) -> str:
    try:
        row = card_info_df[card_info_df['Card Name'] == card_name].iloc[0]
        benefit_columns = card_info_df.columns[8:]  # 8번째 컬럼 이후가 혜택 열
        card_benefits = row[benefit_columns]

        benefit_text = "\n".join(
            f"- {col}: {val}" for col, val in card_benefits.items()
            if pd.notna(val) and str(val).strip() != "0"
        )

        prompt = f"""
{card_name} 카드는 다음과 같은 혜택이 있습니다:
{benefit_text}

이 {card_name} 카드의 주요 혜택을 바탕으로 마케팅 문자 메세지를 생성해주세요.

메세지 길이는 600자 이하로 제한해주세요.

아래 형식을 참고하세요:

---
고객님, [카드 이름]으로 특별한 혜택을 만나보세요! (중략)
---
"""
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"오류 발생: {e}"