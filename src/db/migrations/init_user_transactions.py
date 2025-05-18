import pandas as pd
import pymysql
import os
from dotenv import load_dotenv
from tqdm import tqdm

# .env 환경변수 불러오기
load_dotenv()

# CSV 경로 지정
csv_path = '/Users/james_kyh/Downloads/card_rag_project_collab_all_users/data/user_transactions.csv'
df = pd.read_csv(csv_path)

# MySQL 연결
conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT')),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE'),  # 예: card_recommend
    charset='utf8mb4'
)
cursor = conn.cursor()

# 테이블 생성 (컬럼 타입 추정 기반)
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_transactions (
    SEQ VARCHAR(30) PRIMARY KEY,
    BAS_YH VARCHAR(10),
    ATT_YM VARCHAR(10),
    AGE_encoded INT,
    SEX_CD_encoded INT,
    MBR_RK_encoded INT,
    HOUS_SIDO_NM_encoded INT,
    LIFE_STAGE_encoded INT,
    DIGT_CHNL_REG_YN_encoded INT,
    DIGT_CHNL_USE_YN_encoded INT,
    TOT_USE_AM_mean FLOAT,
    CRDSL_USE_AM_mean FLOAT,
    CNF_USE_AM_mean FLOAT,
    INTERIOR_AM_mean FLOAT,
    INSUHOS_AM_mean FLOAT,
    OFFEDU_AM_mean FLOAT,
    TRVLEC_AM_mean FLOAT,
    FSBZ_AM_mean FLOAT,
    SVCARC_AM_mean FLOAT,
    DIST_AM_mean FLOAT,
    PLSANIT_AM_mean FLOAT,
    CLOTHGDS_AM_mean FLOAT,
    AUTO_AM_mean FLOAT,
    FUNITR_AM_mean FLOAT,
    APPLNC_AM_mean FLOAT,
    HLTHFS_AM_mean FLOAT,
    BLDMNG_AM_mean FLOAT,
    ARCHIT_AM_mean FLOAT,
    OPTIC_AM_mean FLOAT,
    AGRICTR_AM_mean FLOAT,
    LEISURE_S_AM_mean FLOAT,
    LEISURE_P_AM_mean FLOAT,
    CULTURE_AM_mean FLOAT,
    SANIT_AM_mean FLOAT,
    INSU_AM_mean FLOAT,
    OFFCOM_AM_mean FLOAT,
    BOOK_AM_mean FLOAT,
    RPR_AM_mean FLOAT,
    HOTEL_AM_mean FLOAT,
    GOODS_AM_mean FLOAT,
    TRVL_AM_mean FLOAT,
    FUEL_AM_mean FLOAT,
    SVC_AM_mean FLOAT,
    DISTBNP_AM_mean FLOAT,
    DISTBP_AM_mean FLOAT,
    GROCERY_AM_mean FLOAT,
    HOS_AM_mean FLOAT,
    CLOTH_AM_mean FLOAT,
    RESTRNT_AM_mean FLOAT,
    AUTOMNT_AM_mean FLOAT,
    AUTOSL_AM_mean FLOAT,
    KITWR_AM_mean FLOAT,
    FABRIC_AM_mean FLOAT,
    ACDM_AM_mean FLOAT,
    MBRSHOP_AM_mean FLOAT,
    MONTH_DIFF INT,
    TOP_SPENDING_CATEGORY_encoded INT
)
""")

# 자동으로 컬럼 및 placeholder 생성
columns = df.columns.tolist()
columns_str = ', '.join(columns)
placeholders = ', '.join(['%s'] * len(columns))
sql = f"REPLACE INTO user_transactions ({columns_str}) VALUES ({placeholders})"

# 진행률 표시하며 insert 실행
for _, row in tqdm(df.iterrows(), total=len(df), desc="Uploading to MySQL"):
    cursor.execute(sql, tuple(row[col] for col in columns))

# 커밋 및 종료
conn.commit()
cursor.close()
conn.close()

print("✅ user_transactions 테이블 저장 완료!")