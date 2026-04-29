"""
그로스파이낸스 기초재무진단 자동화 시스템
메인 실행 파일
"""
import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="그로스파이낸스 재무진단 시스템", layout="wide")
st.title("그로스파이낸스 기초재무진단 보고서")

# 세션 상태 초기화 함수
def init_session_state():
    defaults = {
        'company_name': '',
        'biz_type': '',
        'ceo_name': '',
        'biz_start_date': '',
        'biz_no': '',
        'phone': '',
        'email': '',
        'address': '',
        'emp_count': '',
        'erp_system': '',
        'exec_summary': '',
        'finance_comment': '',
        'account_comment': '',
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# 각 섹션 import
from section1_info import render_company_info
from section2_upload import render_file_upload
from section3_review import render_data_review
from section3_1_metrics import render_financial_metrics
from section4_diagnosis import render_diagnosis
from section5_comment import render_comments
from section6_report import render_report_generation

# 1. 기업 상세 정보 입력
company_info = render_company_info()

st.markdown("---")

# 2. 사전 진단 및 관리 방향성
check_results, score, selected_dirs, dir_etc, selected_mats = render_diagnosis()

st.markdown("---")

# 3. 자료 업로드
uploaded_file, template_file, df_bs, df_is, years = render_file_upload()

if uploaded_file and df_bs is not None and df_is is not None:
    # 4. 재무 데이터 검토
    render_data_review(df_bs, df_is)
    
    # 4-1. 재무지표 연도별 추이
    bs_metrics, is_metrics, common_metrics, years = render_financial_metrics(df_bs, df_is, years)
    
    # 세션에 지표 데이터 저장 (section5에서 사용)
    st.session_state['bs_metrics'] = bs_metrics
    st.session_state['is_metrics'] = is_metrics
    st.session_state['common_metrics'] = common_metrics
    st.session_state['years'] = years

# 5. 종합의견, 재무분석코멘트, 세부계정분석
exec_summary, finance_comment, account_comment = render_comments()

st.markdown("---")

# 6. 최종보고서 생성
render_report_generation(
    company_info=company_info,
    template_file=template_file,
    check_results=check_results,
    score=score,
    selected_dirs=selected_dirs,
    dir_etc=dir_etc,
    selected_mats=selected_mats,
    exec_summary=exec_summary,
    finance_comment=finance_comment,
    account_comment=account_comment
)