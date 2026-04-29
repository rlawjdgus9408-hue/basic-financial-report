"""
Section 6: 최종보고서 생성
"""
import streamlit as st
import io
import datetime
from docxtpl import DocxTemplate
import time

def render_report_generation(company_info, template_file, check_results, score, selected_dirs, dir_etc, selected_mats, exec_summary, finance_comment, account_comment):
    """최종보고서 생성 렌더링"""
    st.markdown("---")
    st.markdown("### 6. 최종보고서 생성")
    
    if st.button("🚀 최종 보고서 생성"):
        if not template_file:
            st.error("워드 템플릿 파일을 업로드해 주세요.")
            return
        
        # 진행률 표시
        progress_text = "데이터를 분석하여 보고서를 생성 중입니다. 잠시만 기다려주세요..."
        my_bar = st.progress(0, text=progress_text)
        
        for percent_complete in range(100):
            time.sleep(0.015)
            my_bar.progress(percent_complete + 1, text=progress_text)
        
        my_bar.empty()
        st.success("🎉 성공적으로 보고서가 완성되었습니다!")
        
        # 템플릿 렌더링
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
            'erp_system': company_info.get('erp_system', ''),
            'exec_summary': exec_summary,
            'finance_comment': finance_comment,
            'account_comment': account_comment,
            'score': score
        }
        
        # ■ / □ 체크박스 적용
        for i, res in enumerate(check_results):
            num = i + 1
            is_yes = (res == "예")
            context[f'r{num}y'] = "■" if is_yes else "□"
            context[f'r{num}n'] = "■" if not is_yes else "□"
            context[f's{num}y'] = "■" if is_yes else "□"
            context[f's{num}n'] = "■" if not is_yes else "□"
        
        # 방향성 체크박스
        for i, opt in enumerate(["안정적 성장", "투자 유치 (사업확장)", "IPO/M&A 등 Exit"]):
            context[f'd{i+1}'] = "■" if opt in selected_dirs else "□"
        
        # 기타 방향성
        context['d_etc'] = "■" if dir_etc else "□"
        context['d_etc_val'] = dir_etc if dir_etc else "          "
        
        # 보유자료 체크박스
        for i, opt in enumerate(["사업자등록증", "재무제표", "회사소개서", "기타 양식"]):
            context[f'm{i+1}'] = "■" if opt in selected_mats else "□"
        
        # 문서 생성
        doc.render(context)
        output = io.BytesIO()
        doc.save(output)
        
        # 다운로드
        file_name_prefix = company_info.get('company_name', '') if company_info.get('company_name', '') else "진단기업"
        st.download_button(f"📥 {file_name_prefix}_보고서 다운로드", data=output.getvalue(), file_name=f"{file_name_prefix}_재무진단보고서.docx")
    
    # 하단 기능 버튼
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔄 전체 재작성", use_container_width=True):
            st.rerun()
    
    with col_btn2:
        if st.button("🗑️ 모두 지우기", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith(('input_', 'q', 'sel_', 'txt_')):
                    del st.session_state[key]
            st.rerun()
    
    with col_btn3:
        if st.button("🔁 다시 실행하기", use_container_width=True):
            st.rerun()