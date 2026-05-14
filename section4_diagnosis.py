"""
Section 4: 사전 진단 및 관리 방향성
"""
import streamlit as st

def render_diagnosis():
    """사전 진단 및 관리 방향성 렌더링"""
    st.markdown("---")
    st.markdown("### 2. 사전 진단 및 관리 방향성")

    questions = [
        "재무성과(손익/자금 등) 현황 분석/보고(Report)를 매월 받으십니까?",
        "채권 현황(수금 일정 등)을 정확하게 파악하고 계십니까?",
        "현재 (재고/고정)자산에 대한 장부 가치를 정기적으로 파악하고 계십니까?",
        "원가/비용 등에 대한 내부적인 집행 기준(예산 등)이 수립/공유 되고 있습니까?",
        "연말까지(혹은 3개월 이내) 필요한 자금(유동성)에 대하여 정확히 파악하고 계십니까?",
        "자금(출금)과정에서 용도/금액에 대한 통제 절차가 있습니까?",
        "올해 예상되는 재무성과를 숫자(매출/이익 등)로 산출이 가능합니까?",
        "재무적 비상(리스크) 상황 발생에 대한 내부적인 대응 계획이 수립되어 있습니까?",
        "재무성과는 기업 내의 성과관리지표(KPI/OKR 등)와 연관되어 관리되고 있습니까?",
        "투자 유치 시 우리 기업의 미래 지분 가치를 객관적인 근거로 제시할 수 있습니까?"
    ]

    check_results = []
    for i, q in enumerate(questions):
        current = st.session_state.get(f'q{i}', '아니오')

        st.markdown(
            f'<p style="font-size:14px; font-weight:600; color:#212121; '
            f'margin:18px 0 8px 0;">{i+1}. {q}</p>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "예",
                key=f"q{i}_yes",
                use_container_width=True,
                type="primary" if current == "예" else "secondary"
            ):
                st.session_state[f'q{i}'] = '예'
                st.rerun()
        with col2:
            if st.button(
                "아니오",
                key=f"q{i}_no",
                use_container_width=True,
                type="primary" if current == "아니오" else "secondary"
            ):
                st.session_state[f'q{i}'] = '아니오'
                st.rerun()

        check_results.append(current)

    score = check_results.count("예")

    st.markdown("---")
    selected_dirs = st.multiselect("재무관리 방향성", ["안정적 성장", "투자 유치 (사업확장)", "IPO/M&A 등 Exit"], key="sel_dir")
    dir_etc = st.text_input("기타 방향성", value="", key="in_dir_etc")
    selected_mats = st.multiselect("기타 보유자료", ["사업자등록증", "재무제표", "회사소개서", "기타 양식"], key="sel_mat")

    return check_results, score, selected_dirs, dir_etc, selected_mats
