"""
Section 6: 최종보고서 생성
"""
import streamlit as st

def render_report_generation(company_info, template_file, check_results, score, selected_dirs, dir_etc, selected_mats, exec_summary, finance_comment, account_comment):
    """최종보고서 생성 렌더링"""
    st.markdown("---")
    st.markdown("### 6. 최종보고서 생성")
    st.info("💡 사이드바의 '🚀 보고서 생성' 버튼을 클릭하여 보고서를 생성하세요.")
