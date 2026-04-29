"""
Section 5: 종합의견, 재무분석코멘트, 세부계정분석
"""
import streamlit as st
import pandas as pd

def render_comments():
    """종합의견, 재무분석코멘트, 세부계정분석 렌더링"""
    st.markdown("### 5. 종합의견 및 분석 코멘트")
    
    # 선택된 지표가 있으면 표로 표시
    selected_indicators = st.session_state.get('selected_indicators', {})
    
    if selected_indicators and (selected_indicators.get('bs') or selected_indicators.get('is') or selected_indicators.get('common')):
        st.markdown("#### 📊 문서 포함 선택된 재무지표")
        
        # 세션에서 years와 metrics 가져오기
        years = st.session_state.get('years', [])
        bs_metrics = st.session_state.get('bs_metrics', {})
        is_metrics = st.session_state.get('is_metrics', {})
        common_metrics = st.session_state.get('common_metrics', {})
        
        # 선택된 지표들을 표로 구성
        all_selected = selected_indicators.get('bs', []) + selected_indicators.get('is', []) + selected_indicators.get('common', [])
        
        if all_selected and years:
            # 표 데이터 구성
            table_data = []
            for ind in all_selected:
                row_data = {'지표명': ind}
                for yr in years:
                    val = None
                    if bs_metrics.get(yr) and ind in bs_metrics[yr]:
                        val = bs_metrics[yr].get(ind)
                    elif is_metrics.get(yr) and ind in is_metrics[yr]:
                        val = is_metrics[yr].get(ind)
                    elif common_metrics.get(yr) and ind in common_metrics[yr]:
                        val = common_metrics[yr].get(ind)
                    row_data[yr] = f"{val:.2f}" if val is not None else "-"
                table_data.append(row_data)
            
            if table_data:
                df_selected = pd.DataFrame(table_data)
                st.dataframe(df_selected.set_index('지표명'), use_container_width=True)
                st.caption("※ 위 표는 문서 포함을 선택한 지표들입니다.")
    
    exec_summary = st.text_area("📑 종합의견 (Executive Summary)", value=st.session_state.get('exec_summary', ''), height=150, key="txt_exec")
    finance_comment = st.text_area("💰 재무분석 코멘트", value=st.session_state.get('finance_comment', ''), height=100, key="txt_fin")
    account_comment = st.text_area("🔎 세부 계정 분석", value=st.session_state.get('account_comment', ''), key="txt_acc")
    
    return exec_summary, finance_comment, account_comment