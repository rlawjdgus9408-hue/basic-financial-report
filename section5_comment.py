"""
Section 5: 종합의견, 재무분석코멘트, 세부계정분석
"""
import streamlit as st
import pandas as pd

def render_comments():
    """종합의견, 재무분석코멘트, 세부계정분석 렌더링"""
    st.markdown("### 5. 종합의견 및 분석 코멘트")
    
    # 선택된 지표 가져오기
    selected_indicators = st.session_state.get('selected_indicators', {})
    
    # 선택된 지표 기반 표 데이터 저장 (템플릿용)
    selected_indicators_table = ""
    if selected_indicators and (selected_indicators.get('bs') or selected_indicators.get('is') or selected_indicators.get('common')):
        st.markdown("#### 📊 문서 포함 선택된 재무지표")
        
        years = st.session_state.get('years', [])
        bs_metrics = st.session_state.get('bs_metrics', {})
        is_metrics = st.session_state.get('is_metrics', {})
        common_metrics = st.session_state.get('common_metrics', {})
        
        all_selected = selected_indicators.get('bs', []) + selected_indicators.get('is', []) + selected_indicators.get('common', [])
        
        if all_selected and years:
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
                    row_data[yr] = f"{val:,.2f}" if val is not None else "-"
                table_data.append(row_data)
            
            if table_data:
                df_selected = pd.DataFrame(table_data)
                # 테두리가 있는 표 스타일
                st.markdown("""
                <style>
                .dataframe-table {
                    border-collapse: collapse;
                    width: 100%;
                    font-size: 14px;
                }
                .dataframe-table th, .dataframe-table td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }
                .dataframe-table th {
                    background-color: #f0f0f0;
                    font-weight: bold;
                }
                </style>
                """, unsafe_allow_html=True)
                st.dataframe(df_selected.set_index('지표명'), width='stretch')
                st.caption("※ 위 표는 문서 포함을 선택한 지표들입니다.")
                
                # 템플릿용 표 문자열 생성
                selected_indicators_table = "■ 주요 재무지표\n"
                selected_indicators_table += "지표명\t" + "\t".join(years) + "\n"
                for row in table_data:
                    row_str = row['지표명']
                    for yr in years:
                        row_str += f"\t{row.get(yr, '-')}"
                    selected_indicators_table += row_str + "\n"
                
                # 세션에 저장
                st.session_state.selected_indicators_table = selected_indicators_table
    
    # 종합의견 작성 도움말
    st.caption("📝 문단마다 '▣ ' 글머리를 추가하여 작성해 주세요.")
    exec_summary = st.text_area("📑 종합의견 (Executive Summary)", value=st.session_state.get('exec_summary', ''), height=150, key="txt_exec", help="각 문장 앞에 '▣ '를 붙여서 작성해 주세요.")
    
    # 글자수 표시 (A4 1장 기준 약 2000자)
    char_count = len(exec_summary) if exec_summary else 0
    max_chars = 2000
    st.caption(f"📝 글자수: {char_count}/{max_chars}자 (A4 1장 기준)")
    if char_count > max_chars:
        st.warning(f"⚠️ A4 1장 기준({max_chars}자)을 초과했습니다.")
    
    # 재무분석 코멘트 입력창 제거 - 선택된 지표표만 표시
    # finance_comment = st.text_area("💰 재무분석 코멘트", ...) # 제거됨
    
    account_comment = st.text_area("🔎 세부 계정 분석", value=st.session_state.get('account_comment', ''), key="txt_acc")
    
    # finance_comment는 빈 문자열로 반환 (템플릿에서는 선택된 지표표 사용)
    return exec_summary, "", account_comment