"""
Section 1: 기업 상세 정보 입력
"""
import streamlit as st
import pandas as pd
from pathlib import Path


_KSIC_FILE = Path(__file__).parent.parent / "assets" / "reference" / "업종코드-표준산업분류 연계표.xlsx"

def _clear_input(widget_key):
    st.session_state[widget_key] = ''

def _clearable_text_input(label, value, placeholder, key, **kwargs):
    """입력창 오른쪽 안쪽에 값을 한 번에 지우는 버튼을 표시한다."""
    input_col, clear_col = st.columns([1, 0.001], vertical_alignment="center", gap="small")
    with input_col:
        result = st.text_input(label, value=value, placeholder=placeholder, key=key, **kwargs)
    with clear_col:
        st.button("×", key=f"clear_{key}", help=f"{label} 입력 지우기", type="tertiary", on_click=_clear_input, args=(key,))
    return result

@st.cache_data
def load_ksic_data():
    """업종코드 Excel 파일 로드"""
    try:
        df = pd.read_excel(_KSIC_FILE, sheet_name="연계표", header=3)
        
        # 실제 열 인덱스 사용 (0부터 시작)
        # 4: 대분류_표준, 7: 중분류_표준, 9: 소분류_표준
        categories = {}
        for _, row in df.iterrows():
            major = row.iloc[4]  # 대분류_표준
            middle = row.iloc[6]  # 중분류_표준
            minor = row.iloc[8]  # 소분류_표준
            
            if pd.notna(major) and pd.notna(middle) and pd.notna(minor):
                if major not in categories:
                    categories[major] = {}
                if middle not in categories[major]:
                    categories[major][middle] = []
                if minor not in categories[major][middle]:
                    categories[major][middle].append(minor)
        
        return categories
    except Exception as e:
        st.error(f"업종코드 로드 오류: {e}")
        return {
            "농업, 임업 및 어업": {"농업": ["작물 재배업"]},
            "제조업": {"제조업": ["기타 제조업"]},
            "서비스업": {"서비스업": ["기타 서비스업"]}
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
    
    # 대분류 변경 시 중분류, 소분류 초기화
    if current_biz_major != st.session_state.get('prev_biz_major'):
        st.session_state.prev_biz_major = current_biz_major
        middle_keys = list(ksic_categories[current_biz_major].keys())
        st.session_state.input_biz_middle = middle_keys[0] if middle_keys else ""
        if middle_keys:
            minor_list = ksic_categories[current_biz_major][middle_keys[0]]
            st.session_state.input_biz_minor = minor_list[0] if minor_list else ""
    
    with col_info1:
        company_name = _clearable_text_input("진단 기업명", st.session_state.company_name, "예: 주식회사 알파브라더스", "input_co_name")

        # 업종: 드롭다운 or 직접 입력 토글
        if 'biz_type_mode' not in st.session_state:
            st.session_state.biz_type_mode = 'select'

        col_biz_label, col_biz_toggle = st.columns([3, 2])
        with col_biz_label:
            st.markdown("**업종**")
        with col_biz_toggle:
            if st.session_state.biz_type_mode == 'select':
                if st.button("직접 입력", key="btn_biz_direct", use_container_width=True):
                    st.session_state.biz_type_mode = 'direct'
                    st.rerun()
            else:
                if st.button("목록 선택", key="btn_biz_select", use_container_width=True):
                    st.session_state.biz_type_mode = 'select'
                    st.rerun()

        if st.session_state.biz_type_mode == 'select':
            col_biz1, col_biz2, col_biz3 = st.columns(3)
            with col_biz1:
                biz_major = st.selectbox("대분류", valid_keys, index=valid_keys.index(current_biz_major), key="input_biz_major", label_visibility="collapsed")
            with col_biz2:
                middle_keys = list(ksic_categories[biz_major].keys())
                current_middle = st.session_state.get('input_biz_middle')
                if current_middle not in middle_keys:
                    current_middle = middle_keys[0] if middle_keys else ""
                middle_index = middle_keys.index(current_middle) if current_middle in middle_keys else 0
                biz_middle = st.selectbox("중분류", middle_keys, index=middle_index, key="input_biz_middle", label_visibility="collapsed")
            with col_biz3:
                minor_list = ksic_categories[biz_major].get(biz_middle, [])
                current_minor = st.session_state.get('input_biz_minor')
                if current_minor not in minor_list:
                    current_minor = minor_list[0] if minor_list else ""
                minor_index = minor_list.index(current_minor) if current_minor in minor_list else 0
                biz_minor = st.selectbox("소분류", minor_list, index=minor_index, key="input_biz_minor", label_visibility="collapsed")
            biz_type = biz_minor
        else:
            biz_type = st.text_input("업종 직접 입력", value=st.session_state.get('input_biz_direct', ''), placeholder="예: 소프트웨어 개발 및 공급업", key="input_biz_direct", label_visibility="collapsed")
        
        ceo_name = _clearable_text_input("대표자명", st.session_state.ceo_name, "예: 홍길동", "input_ceo_name")
        biz_start_date = _clearable_text_input("사업개시일", st.session_state.biz_start_date, "예: 2024-01-01", "input_biz_start")
        biz_no = _clearable_text_input("사업자번호", st.session_state.biz_no, "예: 000-00-00000", "input_biz_no")

    with col_info2:
        phone = _clearable_text_input("연락처", st.session_state.phone, "예: 000-0000-0000", "input_phone")

        # 이메일: 한 줄로 표시 (도메인 앞에 @)
        col_email1, col_email2, col_email3 = st.columns([3, 1, 2])
        with col_email1:
            email_local = _clearable_text_input("이메일", st.session_state.email.split('@')[0] if '@' in st.session_state.email else st.session_state.email, "example", "input_email_local")
        with col_email2:
            st.markdown("<p style='margin-top:34px; font-size:16px; text-align:center; color:#363636;'>@</p>", unsafe_allow_html=True)
        with col_email3:
            email_domain = st.selectbox("도메인",
                ["gmail.com", "naver.com", "kakao.com", "hanmail.net", "nate.com", "hotmail.com", "icloud.com", "직접 입력"],
                index=7, key="input_email_domain", label_visibility="hidden")
        if email_domain == "직접 입력":
            email_domain = _clearable_text_input("도메인 직접 입력", st.session_state.get('input_email_custom', ''), "example.com", "input_email_custom", label_visibility="collapsed")
        full_email = f"{email_local}@{email_domain}" if email_local and email_domain else ""

        address = _clearable_text_input("주소", st.session_state.address, "예: 서울시 금천구 가산디지털1로", "input_address")
        emp_count = _clearable_text_input("임직원 수 (숫자만)", st.session_state.emp_count, "예: 10", "input_emp_count")

        # 활용시스템: 다중 선택 + 기타 직접 입력
        erp_options = ["더존계열", "더존 위하고", "세무사랑", "경리나라", "이카운트", "기타"]
        current_erp = st.session_state.get('erp_system', [])
        if isinstance(current_erp, str):
            current_erp = [current_erp] if current_erp else []

        erp_system = st.multiselect("활용 시스템 (다중 선택)", erp_options, default=current_erp, key="input_erp")
        
        # 기타 선택 시 직접 입력
        if "기타" in erp_system:
            erp_etc = _clearable_text_input("기타 시스템 직접 입력", st.session_state.get('erp_etc', ''), "시스템명 입력", "input_erp_etc")
            if erp_etc:
                erp_system = [e if e != "기타" else erp_etc for e in erp_system]

    note_col, clear_note_col = st.columns([1, 0.001], vertical_alignment="center", gap="small")
    with note_col:
        special_note = st.text_area(
            "특이사항",
            value=st.session_state.get('special_note', ''),
            placeholder="기업 관련 특이사항을 자유롭게 입력하세요",
            height=80,
            key="input_special_note"
        )
    with clear_note_col:
        st.button("×", key="clear_input_special_note", help="특이사항 입력 지우기", type="tertiary", on_click=_clear_input, args=("input_special_note",))

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
        'erp_system': erp_system,
        'special_note': special_note
    }