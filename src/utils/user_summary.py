def summarize_user_info(user: dict) -> str:
    # 카테고리 코드 매핑 테이블 추가
    category_mapping = {
        0: "ACDM_AM (학원비)",
        1: "AGRICTR_A (농장)",
        2: "APPLIC_A (가전제품)",
        3: "ARCHIT_AM (건축/시재)",
        4: "AUTOMT_차 (차 히스토리)",
        5: "AUTOSL_새 (자동차딜러)",
        6: "BLDMNG_건 (건물관리)",
        7: "BOOK_AM (서적)",
        8: "CLOTH_AM (의류)",
        9: "CULTURE_문 (문화/취미)",
        10: "DISTNBP_유 (유통 일반)",
        11: "DISTIB_쇼 (쇼핑몰)",
        12: "FABRIC_AN (직물)",
        13: "FUEL_AM (연료/대체)",
        14: "FUNITR_AN (가구)",
        15: "GOODS_AN (가정용품)",
        16: "GROCERY_음 (식료품)",
        17: "HOS_AM (병원)",
        18: "HOTEL_AM (숙박업)",
        19: "INSU_AM (보험)",
        20: "KITWR_AM (주방용품)",
        21: "LEISURE_P (레저활동)",
        22: "LEISURE_S (스포츠)",
        23: "MBRSHOP_멤 (멤버쉽피)",
        24: "OFFEDU_AM (교육/학원)",
        25: "OPTIC_AM (광학제품)",
        26: "RESTRNT_외 (외식업)",
        27: "RPR_AM (수리서비스)",
        28: "SAINT_AM (성지)",
        29: "SVC_AM (용역서비스)",
        30: "TRVL_AM (여행업)"
    }
    
    # 기본 정보
    base_info = f"""
**👤 기본 정보**
- 연령대: {user['AGE_encoded']*10}대
- 성별: {"여성" if user['SEX_CD_encoded'] == 1 else "남성"}
- 디지털 채널 사용: {"예" if user['DIGT_CHNL_USE_YN_encoded'] == 1 else "아니오"}
"""

    # 소비 카테고리별 항목 선택적으로 추가
    dynamic_info = "**📊 주요 소비 항목 (월 평균)**\n"
    category_fields = {
        "총 이용 금액": "TOT_USE_AM_mean",
        "쇼핑": "CLOTH_AM_mean",
        "외식": "RESTRNT_AM_mean",
        "여행": "TRVL_AM_mean",
        "보험": "INSU_AM_mean",
        "병원": "HOS_AM_mean",
        "문화": "CULTURE_AM_mean",
        "교육": "OFFEDU_AM_mean",
        "레저": "LEISURE_P_AM_mean"
    }

    for label, col in category_fields.items():
        value = user.get(col, 0)
        if value and value > 0:
            dynamic_info += f"- {label}: {int(value*1000):,}원\n"

    # 대표 카테고리
    top_cat = user.get('TOP_SPENDING_CATEGORY_encoded')
    
    # 카테고리 코드와 이름 매핑
    top_cat_name = ""
    if top_cat is not None:
        # 정수로 변환 (데이터베이스에서 문자열로 저장되었을 수 있음)
        try:
            top_cat_int = int(top_cat)
            if top_cat_int in category_mapping:
                top_cat_name = f" ({category_mapping[top_cat_int]})"
        except (ValueError, TypeError):
            pass
    
    top_cat_str = f"\n**🏷️ 대표 소비 카테고리**\n- 코드: {top_cat}{top_cat_name}" if top_cat is not None else ""

    return base_info + "\n" + dynamic_info + top_cat_str