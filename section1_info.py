"""
Section 1: 기업 상세 정보 입력
"""
import streamlit as st
import pandas as pd

@st.cache_data
def load_ksic_data():
    """업종코드 CSV 파일 로드"""
    try:
        df = pd.read_csv("업종코드_참조.csv", encoding="utf-8")
        categories = df.groupby("업태")["업종코드"].apply(list).to_dict()
        return categories
    except:
        return {
            "농업": ["곡물 재배", "축산", "농업 서비스", "임업", "어업"],
            "제조업": ["Food 제조", "전자부품 제조", "자동차 제조"],
            "서비스": ["전문 서비스", "교육 서비스", "의료 서비스"]
        }

def render_company_info():
    """기업 상세 정보 입력 렌더링"""
    st.markdown("### 1. 기업 상세 정보 입력")
    col_info1, col_info2 = st.columns(2)
    
    ksic_categories = load_ksic_data()
    
    # 대분류 변경 시 소분류 초기화
    if 'prev_biz_major' not in st.session_state:
        st.session_state.prev_biz_major = list(ksic_categories.keys())[0]
    
    valid_keys = list(ksic_categories.keys())
    current_biz_major = st.session_state.get('input_biz_major')
    if current_biz_major not in valid_keys:
        current_biz_major = valid_keys[0]
    
    if current_biz_major != st.session_state.prev_biz_major:
        st.session_state.prev_biz_major = current_biz_major
        st.session_state.input_biz_minor = ksic_categories[current_biz_major][0]
    
    with col_info1:
        company_name = st.text_input("🏢 진단 기업명", value=st.session_state.company_name, placeholder="예:Growth파이낸스", key="input_co_name")
        
        # 업종: 업태/업종코드 선택
        col_biz1, col_biz2 = st.columns(2)
        with col_biz1:
            biz_major = st.selectbox("🏭 업태", valid_keys, index=valid_keys.index(current_biz_major), key="input_biz_major")
        with col_biz2:
            biz_minor = st.selectbox("🏭 업종코드", ksic_categories[biz_major], key="input_biz_minor")
        biz_type = f"{biz_major} > {biz_minor}"
        
        ceo_name = st.text_input("👤 대표자명", value=st.session_state.ceo_name, placeholder="예:홍길동", key="input_ceo_name")
        biz_start_date = st.text_input("📅 사업개시일", value=st.session_state.biz_start_date, placeholder="예:2024-01-01", key="input_biz_start")
        biz_no = st.text_input("🔢 사업자번호", value=st.session_state.biz_no, placeholder="예:000-00-00000", key="input_biz_no")
    
    with col_info2:
        phone = st.text_input("📞 연락처", value=st.session_state.phone, placeholder="예:000-0000-0000(-없이 입력해주세요)", key="input_phone")
        
        # 이메일: 한 줄로 표시 (도메인 앞에 @)
        col_email1, col_email2, col_email3 = st.columns([3, 1, 2])
        with col_email1:
            email_local = st.text_input("📧 이메일", value=st.session_state.email.split('@')[0] if '@' in st.session_state.email else st.session_state.email, placeholder="example", key="input_email_local")
        with col_email2:
            st.markdown("<h4 style='margin-top: 8px;'>@</h4>", unsafe_allow_html=True)
        with col_email3:
            email_domain = st.selectbox("도메인", 
                ["gmail.com", "naver.com", "kakao.com", "hanmail.net", "nate.com", "hotmail.com", "icloud.com", "직접 입력"], 
                index=7, key="input_email_domain")
        if email_domain == "직접 입력":
            email_domain = st.text_input("직접 입력할 도메인", placeholder="example.com", key="input_email_custom")
        full_email = f"{email_local}@{email_domain}" if email_local and email_domain else ""
        
        address = st.text_input("📍 주소", value=st.session_state.address, placeholder="예:서울시 금천구 가산디지털1로", key="input_address")
        emp_count = st.text_input("👥 임직원 수 (숫자만)", value=st.session_state.emp_count, placeholder="예:10", key="input_emp_count")
        
        # 활용시스템: 선택창
        erp_options = ["이카운트", "더존위고", "더존비즈", "ERP", "ACS", "원스", "고려시스템", "기타"]
        erp_system = st.selectbox("🖥️ 활용 시스템", erp_options, index=erp_options.index(st.session_state.erp_system) if st.session_state.erp_system in erp_options else 0, key="input_erp")
    
    return {
        'company_name': company_name,
        'biz_type': biz_type,
        'ceo_name': ceo_name,
        'biz_start_date': biz_start_date,
        'biz_no': biz_no,
        'phone': phone,
        'email': full_email,
        'address': address,
        'emp_count': emp_count,
        'erp_system': erp_system
    }