"""
Section 3: 재무 데이터 검토
"""
import streamlit as st
import pandas as pd

def render_data_review(df_bs, df_is):
    """재무 데이터 검토 렌더링"""
    st.markdown("### 3. 재무 데이터 검토")
    tab_bs, tab_is = st.tabs(["🏛️ 재무상태표 (BS)", "📈 손익계산서 (IS)"])
    tab_bs.data_editor(df_bs, use_container_width=True, key="bs_editor")
    tab_is.data_editor(df_is, use_container_width=True, key="is_editor")