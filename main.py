"""
그로스파이낸스 기초재무진단 자동화 시스템
메인 실행 파일
"""
import streamlit as st
import pandas as pd
import io
import time
import datetime
from docxtpl import DocxTemplate

# 페이지 설정
st.set_page_config(page_title="그로스파이낸스 재무진단 시스템", layout="wide")

# 사이드바 생성
st.sidebar.title("📋 메뉴")
st.sidebar.markdown("---")

# 네비게이션 링크
nav_items = [
    ("1. 기업 상세 정보 입력", "sec1"),
    ("2. 사전 진단 및 관리 방향성", "sec2"),
    ("3. 자료 업로드", "sec3"),
    ("4. 재무 데이터 검토", "sec4"),
    ("5. 종합의견 및 분석 코멘트", "sec5"),
    ("6. 최종보고서 생성", "sec6"),
]

for label, key in nav_items:
    # 링크 형태로 네비게이션
    st.sidebar.markdown(f"""
    <a href="#{key}" style="text-decoration: none; color: inherit;">
        <div class="nav-button">{label}</div>
    </a>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")

# 리셋 버튼 그룹
st.sidebar.subheader("🔧 작업")

if st.sidebar.button("🔄 전체재작성", use_container_width=True):
    # 모든 세션 상태 초기화
    for key in list(st.session_state.keys()):
        if key not in ['selected_indicators']:
            st.session_state[key] = ''
    st.rerun()

if st.sidebar.button("🗑️ 모두지우기", use_container_width=True):
    # 세션 상태 전체 초기화
    for key in list(st.session_state.keys()):
        st.session_state[key] = ''
    st.rerun()

if st.sidebar.button("▶️ 다시 실행하기", use_container_width=True):
    st.rerun()

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
st.markdown('<div id="sec1"></div>', unsafe_allow_html=True)
company_info = render_company_info()

st.markdown("---")

# 2. 사전 진단 및 관리 방향성
st.markdown('<div id="sec2"></div>', unsafe_allow_html=True)
check_results, score, selected_dirs, dir_etc, selected_mats = render_diagnosis()

st.markdown("---")

# 3. 자료 업로드
st.markdown('<div id="sec3"></div>', unsafe_allow_html=True)
uploaded_file, template_file, df_bs, df_is, years = render_file_upload()

if uploaded_file and df_bs is not None and df_is is not None:
    # 4. 재무 데이터 검토
    st.markdown('<div id="sec4"></div>', unsafe_allow_html=True)
    render_data_review(df_bs, df_is)
    
    # 4-1. 재무지표 연도별 추이
    bs_metrics, is_metrics, common_metrics, years = render_financial_metrics(df_bs, df_is, years)
    
    # 세션에 지표 데이터 저장 (section5에서 사용)
    st.session_state['bs_metrics'] = bs_metrics
    st.session_state['is_metrics'] = is_metrics
    st.session_state['common_metrics'] = common_metrics
    st.session_state['years'] = years

# 5. 종합의견, 재무분석코멘트, 세부계정분석
st.markdown('<div id="sec5"></div>', unsafe_allow_html=True)
exec_summary, finance_comment, account_comment = render_comments()

st.markdown("---")

# 6. 최종보고서 생성
st.markdown('<div id="sec6"></div>', unsafe_allow_html=True)
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

# 사이드바 보고서 생성 (모든 변수가 정의된 후 실행)
st.sidebar.markdown("---")
st.sidebar.subheader("📄 최종보고서")

if template_file:
    if st.sidebar.button("🚀 보고서 생성", use_container_width=True):
        progress_text = "데이터를 분석하여 보고서를 생성 중입니다. 잠시만 기다려주세요..."
        my_bar = st.sidebar.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.015)
            my_bar.progress(percent_complete + 1, text=progress_text)

        my_bar.empty()

        doc = DocxTemplate(template_file)

        context = {
            'today': datetime.datetime.now().strftime("%Y. %m."),
            'company_name': company_info.get('company_name', ''),
            'biz_type': company_info.get('biz_type', ''),
            'ceo_name': company_info.get('ceo_name', ''),
            'biz_start_date': company_info.get('biz_start_date', ''),
            'biz_no': company_info.get('biz_no', ''),
            'phone': company_info.get('phone', ''),
            'email': company_info.get('email', ''),
            'address': company_info.get('address', ''),
            'emp_count': company_info.get('emp_count', ''),
            'erp_system': ', '.join(company_info.get('erp_system', [])) if isinstance(company_info.get('erp_system'), list) else company_info.get('erp_system', ''),
            'exec_summary': exec_summary,
            'finance_comment': st.session_state.get('selected_indicators_table', ''),
            'account_comment': account_comment,
            'score': score
        }

        for i, res in enumerate(check_results):
            num = i + 1
            is_yes = (res == "예")
            context[f'r{num}y'] = "■" if is_yes else "□"
            context[f'r{num}n'] = "■" if not is_yes else "□"
            context[f's{num}y'] = "■" if is_yes else "□"
            context[f's{num}n'] = "■" if not is_yes else "□"

        for i, opt in enumerate(["안정적 성장", "투자 유치 (사업확장)", "IPO/M&A 등 Exit"]):
            context[f'd{i+1}'] = "■" if opt in selected_dirs else "□"

        context['d_etc'] = "■" if dir_etc else "□"
        context['d_etc_val'] = dir_etc if dir_etc else "          "

        for i, opt in enumerate(["사업자등록증", "재무제표", "회사소개서", "기타 양식"]):
            context[f'm{i+1}'] = "■" if opt in selected_mats else "□"

        doc.render(context)
        output = io.BytesIO()
        doc.save(output)

        file_name_prefix = company_info.get('company_name', '') or "진단기업"
        st.session_state['report_bytes'] = output.getvalue()
        st.session_state['report_filename'] = f"{file_name_prefix}_재무진단보고서.docx"
        st.session_state['report_company'] = file_name_prefix
        st.sidebar.success("🎉 보고서 생성 완료!")

    if st.session_state.get('report_bytes'):
        file_name_prefix = st.session_state.get('report_company', '진단기업')
        st.sidebar.download_button(
            f"📥 {file_name_prefix}_보고서 다운로드",
            data=st.session_state['report_bytes'],
            file_name=st.session_state['report_filename'],
            use_container_width=True
        )