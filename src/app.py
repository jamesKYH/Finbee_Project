import streamlit as st
from dotenv import load_dotenv
import os
import re

# ✅ 필요한 모듈 불러오기
from db.db_utils import get_user_profile, get_recommended_cards
from utils.user_summary import summarize_user_info
from llm.marketing_generator import summarize_card_benefits_openai
from llm.rag_answer import ask_card_rag

# ✅ 응답에서 카드 정보 추출하는 함수
def extract_card_info(response):
    # 카드 정보를 추출하는 정규식 패턴
    card_pattern = r'(\d+)\.\s+카드명:\s+([^\n]+)'
    cards = re.findall(card_pattern, response)
    return cards

# ✅ 카드 설명 컨테이너 스타일 정의
CARD_CONTAINER_STYLE = """
<div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.08);">
    <h4 style="color: #1a73e8; margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px; font-size: 18px;">{card_num}. {card_name}</h4>
    {card_text}
</div>
"""

# ✅ 카드 설명 텍스트 정리 함수
def clean_card_description(text):
    # 불필요한 줄바꿈 제거
    text = text.strip()
    
    # 여러 줄 바꿈을 하나로 통합
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 광고 문구로 보이는 부분 제거 (📝 이모지로 시작하는 부분)
    text = re.sub(r'📝\s*.*?(\n|$)', '', text)
    
    # 광고 문구 관련 키워드가 포함된 문장 제거
    ad_keywords = ['광고', '광고 문구', '마케팅', '홍보']
    for keyword in ad_keywords:
        text = re.sub(f'.*{keyword}.*(\n|$)', '', text)
    
    # 입력 텍스트에서 주요 섹션 추출
    card_company = ""
    benefits = []
    recommendation = ""
    
    # 카드사 및 유형 추출
    company_match = re.search(r'카드사 및 유형:?\s*([^•\n-]+)', text)
    if company_match:
        card_company = company_match.group(1).strip()
    
    # 혜택 항목 추출 - 모든 글머리 기호 패턴 처리
    benefit_section = re.search(r'관련 혜택:?(.*?)(?=추천 이유:|$)', text, re.DOTALL)
    if benefit_section:
        benefit_text = benefit_section.group(1).strip()
        # 글머리 기호로 시작하는 라인 찾기
        benefit_items = re.findall(r'(?:^|\n)\s*[•\-*]\s*(.*?)(?=\n\s*[•\-*]|\n\s*추천 이유:|$)', benefit_text, re.DOTALL)
        benefits = [item.strip() for item in benefit_items if item.strip()]
    
    # 추천 이유 추출
    reason_match = re.search(r'추천 이유:?\s*(.*?)$', text, re.DOTALL)
    if reason_match:
        recommendation = reason_match.group(1).strip()
    
    # HTML 구성
    html_parts = []
    
    # CSS 스타일
    html_parts.append("""<style>
.card-section {
    margin-bottom: 15px;
}
.section-title {
    font-weight: bold;
    color: #1a73e8;
    margin-bottom: 8px;
    font-size: 16px;
}
.company-info {
    background-color: #f8f9fa;
    padding: 8px 12px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 500;
    color: #333;
}
.benefits-list {
    margin: 0;
    padding-left: 25px;
}
.benefits-list li {
    margin-bottom: 8px;
    color: #333;
    line-height: 1.5;
}
.recommendation {
    padding-left: 10px;
    color: #555;
    font-style: italic;
    border-left: 3px solid #e0e0e0;
    margin-top: 5px;
}
</style>""")
    
    # 카드사 및 유형 섹션
    if card_company:
        html_parts.append("""<div class="card-section">
<div class="section-title">카드사 및 유형</div>
<div class="company-info">{}</div>
</div>""".format(card_company))
    
    # 관련 혜택 섹션
    if benefits:
        benefits_html = '<ul class="benefits-list">'
        for benefit in benefits:
            benefits_html += f'<li>{benefit}</li>'
        benefits_html += '</ul>'
        
        html_parts.append("""<div class="card-section">
<div class="section-title">관련 혜택</div>
{}
</div>""".format(benefits_html))
    
    # 추천 이유 섹션
    if recommendation:
        html_parts.append("""<div class="card-section">
<div class="section-title">추천 이유</div>
<div class="recommendation">{}</div>
</div>""".format(recommendation))
    
    return ''.join(html_parts)

# ✅ 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "image_info" not in st.session_state:
    st.session_state.image_info = []
if "ad_copy_loaded" not in st.session_state:
    st.session_state.ad_copy_loaded = False
if "user_summary_loaded" not in st.session_state:
    st.session_state.user_summary_loaded = False
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "recommended_cards" not in st.session_state:
    st.session_state.recommended_cards = []
if "ad_copies" not in st.session_state:
    st.session_state.ad_copies = {}
if "user_summary" not in st.session_state:
    st.session_state.user_summary = ""

# ✅ 환경 변수 로드
load_dotenv()

# ✅ 페이지 설정
st.set_page_config(page_title="finBee 딱카 - 내게 맞는 카드 추천", page_icon="💳")

# ✅ 상단 타이틀 영역
col1, col2 = st.columns([7, 1])  # 7:1 비율로 텍스트 : 이미지

with col1:
    st.markdown("<h1 style='text-align: center;'>딱 맞는 카드, finBee 딱카에서.</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>내게 맞는 카드, 직접 찾아보세요.</h4>", unsafe_allow_html=True)

with col2:
    # 현재 스크립트 파일의 절대 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 프로젝트 루트 디렉토리 (src의 상위 디렉토리)
    root_dir = os.path.dirname(current_dir)
    # 이미지 파일 경로
    image_path = os.path.join(root_dir, "assets", "finbee.png")
    
    # 파일 존재 여부 확인
    if os.path.exists(image_path):
        st.image(image_path, width=80)
    else:
        st.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")

# ✅ 1. 사용자 ID 입력
user_id = st.text_input("👤 사용자 ID를 입력하세요:", key="user_id")

# ✅ 사용자 정보 표시
if user_id:
    # 사용자 ID가 변경되었을 때만 데이터를 다시 로드
    if user_id != st.session_state.current_user_id:
        st.session_state.current_user_id = user_id
        st.session_state.user_info = get_user_profile(user_id)
        st.session_state.ad_copy_loaded = False
        st.session_state.user_summary_loaded = False
        st.session_state.recommended_cards = []
        st.session_state.ad_copies = {}
        st.session_state.user_summary = ""
        # 챗봇 히스토리 초기화
        st.session_state.chat_history = []
        st.session_state.feedback = []
        st.session_state.image_info = []

    if st.session_state.user_info:
        st.divider()
        
        # ✅ 전체 레이아웃 구성 - 탭으로 분리
        tab1, tab2 = st.tabs(["📊 프로필 및 추천 카드", "🤖 카드 상담 챗봇"])
        
        with tab1:
            # ✅ 2. 광고 문구 + 소비성향 나란히 배치
            st.markdown("## ✉️ 당신이 받은 광고 문구 & 📊 소비 성향")

            left_col, right_col = st.columns(2)

            with left_col:
                st.markdown("### 💳 추천 카드 광고 문구")
                
                # 광고 문구가 로드되지 않은 경우에만 로드
                if not st.session_state.ad_copy_loaded:
                    st.session_state.recommended_cards = get_recommended_cards(user_id)
                    
                    if st.session_state.recommended_cards:
                        for card_name in st.session_state.recommended_cards:
                            with st.spinner(f"{card_name} 카드 광고 문구 생성 중..."):
                                if card_name not in st.session_state.ad_copies:
                                    st.session_state.ad_copies[card_name] = summarize_card_benefits_openai(card_name)
                    
                        st.session_state.ad_copy_loaded = True
                    else:
                        st.warning("추천된 카드 광고 문구가 없습니다.")
                
                # 저장된 광고 문구 표시
                for card_name in st.session_state.recommended_cards:
                    ad_copy = st.session_state.ad_copies.get(card_name, "광고 문구를 불러올 수 없습니다.")
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #ccc; border-radius: 10px; padding: 15px; background-color: #f9f9f9;">
                            <h4 style="margin-top:0;">💳 {card_name}</h4>
                            <p style="font-size:16px;">📝 {ad_copy}</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            with right_col:
                st.markdown("### 📊 당신의 소비 성향 요약")
                
                # 소비 성향 요약이 로드되지 않은 경우에만 로드
                if not st.session_state.user_summary_loaded:
                    st.session_state.user_summary = summarize_user_info(st.session_state.user_info)
                    st.session_state.user_summary_loaded = True
                    
                st.markdown(st.session_state.user_summary)
        
        with tab2:
            # ✅ 3. 챗봇으로 이동
            st.markdown("## 🤖 다른 혜택의 카드를 찾고 싶으신가요? 챗봇에게 물어보세요!")

            # ✅ 사용자 질문 입력 및 처리
            user_input = st.chat_input("궁금한 카드 혜택 질문을 입력하세요. (예: 쇼핑 혜택 좋은 카드 뭐야?)")

            # 새 질문이 입력되면 처리
            if user_input:
                # 이미 처리된 질문인지 확인
                is_new_question = True
                for old_question, _ in st.session_state.chat_history:
                    if old_question == user_input:
                        is_new_question = False
                        break
                
                # 새 질문이면 처리
                if is_new_question:
                    # 사용자 메시지 표시
                    with st.chat_message("user"):
                        st.markdown(f"**🙋‍♂️ 질문:** {user_input}")
                    
                    # 응답 메시지 컨테이너 생성
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        with st.spinner("카드 추천 중입니다..."):
                            # 스트리밍 모드로 응답 요청
                            stream, image_info, _ = ask_card_rag(user_input, user_id=user_id, stream=True)
                            
                            # 스트리밍 응답 처리
                            for chunk in stream:
                                if chunk.choices[0].delta.content is not None:
                                    full_response += chunk.choices[0].delta.content
                                    # 실시간으로 응답 업데이트
                                    message_placeholder.markdown(f"**🤖 답변:** {full_response}▌")
                        
                        # 최종 응답 표시 - 카드 이미지와 설명을 통합하기 위해 여기서는 표시하지 않음
                        # message_placeholder.markdown(f"**🤖 답변:** {full_response}")
                    
                    # 카드 이미지와 설명을 통합하여 표시
                    if image_info:
                        # 응답에서 카드 번호와 카드명 추출
                        card_matches = extract_card_info(full_response)
                        card_names = [card[1].strip() for card in card_matches]
                        
                        # 응답을 카드 단위로 분할
                        card_sections = re.split(r'\d+\.\s+카드명:', full_response)
                        
                        # 전체 응답에서 카드 정보 부분을 제외한 소개/결론 부분 추출
                        intro_text = card_sections[0] if card_sections else ""
                        
                        # 광고 문구 관련 키워드가 포함된 부분 제거
                        ad_keywords = ['광고', '광고 문구', '마케팅', '홍보']
                        for keyword in ad_keywords:
                            intro_text = re.sub(f'.*{keyword}.*(\n|$)', '', intro_text)
                        
                        # 소개 부분 표시 (광고 문구가 아닌 경우에만)
                        intro_text = intro_text.strip()
                        if intro_text and not any(keyword in intro_text for keyword in ad_keywords):
                            message_placeholder.markdown(f"**🤖 답변:** {intro_text}")
                        
                        if len(card_sections) > 1 and len(card_names) > 0:
                            # 각 카드 섹션에 대해 이미지와 설명을 나란히 표시
                            for j, card_name in enumerate(card_names):
                                # 이미지 정보 찾기
                                matching_card = None
                                for card in image_info:
                                    if card_name in card.get("card_name", ""):
                                        matching_card = card
                                        break
                                
                                # 매칭되는 카드가 없으면 인덱스에 맞는 카드 사용
                                if not matching_card and len(image_info) > j:
                                    matching_card = image_info[j]
                                # 인덱스가 범위를 벗어나면 첫 번째 카드 사용
                                elif not matching_card and len(image_info) > 0:
                                    matching_card = image_info[0]
                                
                                if matching_card and matching_card.get("image_url"):
                                    # 카드 설명 텍스트 추출
                                    card_section_text = ""
                                    if j+1 < len(card_sections):
                                        card_section_text = card_sections[j+1]
                                    
                                    # 설명 텍스트에서 주요 부분만 추출하여 가독성 향상
                                    # 텍스트 정리 함수 적용
                                    card_section_text = clean_card_description(card_section_text)
                                    
                                    # 이미지와 설명을 나란히 배치
                                    img_col, desc_col = st.columns([1, 3])
                                    with img_col:
                                        st.image(
                                            matching_card["image_url"],
                                            caption=matching_card.get("card_name", "카드 이름 없음"),
                                            width=150
                                        )
                                    with desc_col:
                                        st.markdown(CARD_CONTAINER_STYLE.format(card_num=j+1, card_name=card_name, card_text=card_section_text), unsafe_allow_html=True)
                    
                    # 피드백 버튼 표시
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👍 만족해요", key=f"like_new"):
                            st.success("감사합니다! 😊")
                    with col2:
                        if st.button("👎 아쉬워요", key=f"dislike_new"):
                            st.info("더 나은 추천을 위해 노력할게요!")
                    
                    # 세션 상태에 저장
                    st.session_state.chat_history.append((user_input, full_response))
                    st.session_state.feedback.append(None)
                    st.session_state.image_info.append(image_info)

            # ✅ 이전 대화 히스토리 출력 (가장 최근 대화 제외)
            for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history[:-1] if user_input and is_new_question else st.session_state.chat_history):
                with st.chat_message("user"):
                    st.markdown(f"**🙋‍♂️ 질문:** {user_msg}")

                with st.chat_message("assistant"):
                    # 응답 표시
                    # st.markdown(f"**🤖 답변:** {bot_msg}")
                    
                    # 카드 이미지와 설명을 통합하여 표시
                    if i < len(st.session_state.image_info) and st.session_state.image_info[i]:
                        # 응답에서 카드 번호와 카드명 추출
                        card_matches = extract_card_info(bot_msg)
                        card_names = [card[1].strip() for card in card_matches]
                        
                        # 응답을 카드 단위로 분할
                        card_sections = re.split(r'\d+\.\s+카드명:', bot_msg)
                        
                        # 전체 응답에서 카드 정보 부분을 제외한 소개/결론 부분 추출
                        intro_text = card_sections[0] if card_sections else ""
                        
                        # 광고 문구 관련 키워드가 포함된 부분 제거
                        ad_keywords = ['광고', '광고 문구', '마케팅', '홍보']
                        for keyword in ad_keywords:
                            intro_text = re.sub(f'.*{keyword}.*(\n|$)', '', intro_text)
                        
                        # 소개 부분 표시 (광고 문구가 아닌 경우에만)
                        intro_text = intro_text.strip()
                        if intro_text and not any(keyword in intro_text for keyword in ad_keywords):
                            st.markdown(f"**🤖 답변:** {intro_text}")
                        
                        if len(card_sections) > 1 and len(card_names) > 0:
                            # 각 카드 섹션에 대해 이미지와 설명을 나란히 표시
                            for j, card_name in enumerate(card_names):
                                # 이미지 정보 찾기
                                matching_card = None
                                for card in st.session_state.image_info[i]:
                                    if card_name in card.get("card_name", ""):
                                        matching_card = card
                                        break
                                
                                # 매칭되는 카드가 없으면 인덱스에 맞는 카드 사용
                                if not matching_card and len(st.session_state.image_info[i]) > j:
                                    matching_card = st.session_state.image_info[i][j]
                                # 인덱스가 범위를 벗어나면 첫 번째 카드 사용
                                elif not matching_card and len(st.session_state.image_info[i]) > 0:
                                    matching_card = st.session_state.image_info[i][0]
                                
                                if matching_card and matching_card.get("image_url"):
                                    # 카드 설명 텍스트 추출
                                    card_section_text = ""
                                    if j+1 < len(card_sections):
                                        card_section_text = card_sections[j+1]
                                    
                                    # 설명 텍스트에서 주요 부분만 추출하여 가독성 향상
                                    # 텍스트 정리 함수 적용
                                    card_section_text = clean_card_description(card_section_text)
                                    
                                    # 이미지와 설명을 나란히 배치
                                    img_col, desc_col = st.columns([1, 3])
                                    with img_col:
                                        st.image(
                                            matching_card["image_url"],
                                            caption=matching_card.get("card_name", "카드 이름 없음"),
                                            width=150
                                        )
                                    with desc_col:
                                        st.markdown(CARD_CONTAINER_STYLE.format(card_num=j+1, card_name=card_name, card_text=card_section_text), unsafe_allow_html=True)
                    else:
                        # 이미지 정보가 없는 경우 전체 응답 표시
                        st.markdown(f"**🤖 답변:** {bot_msg}")
                    
                    # ✅ 피드백 버튼 표시
                    if i < len(st.session_state.feedback) and st.session_state.feedback[i] is None:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("👍 만족해요", key=f"like_{i}"):
                                st.session_state.feedback[i] = "like"
                                st.success("감사합니다! 😊")
                        with col2:
                            if st.button("👎 아쉬워요", key=f"dislike_{i}"):
                                st.session_state.feedback[i] = "dislike"
                                st.info("더 나은 추천을 위해 노력할게요!")
                    elif i < len(st.session_state.feedback):
                        feedback_text = "👍 만족한 응답" if st.session_state.feedback[i] == "like" else "👎 아쉬운 응답"
                        st.caption(f"피드백: {feedback_text}")

    else:
        st.warning("해당 사용자 정보를 찾을 수 없습니다.")