"""
Section 3: 재무 데이터 검토
"""
import streamlit as st
import pandas as pd


def _format_amount_table(df, divisor):
    display_df = df.copy()
    for column in display_df.columns:
        if column == "계정과목":
            continue
        display_df[column] = pd.to_numeric(display_df[column], errors="coerce").map(
            lambda value: f"{value / divisor:,.0f}" if pd.notna(value) else "-"
        )
    return display_df


def render_data_review(df_bs, df_is):
    """재무 데이터 검토 렌더링"""
    st.markdown("### 4. 재무 데이터 검토")
    unit_options = {"원": 1, "만원": 10_000, "백만원": 1_000_000}
    unit = st.selectbox("금액 표시 단위", list(unit_options), index=0, key="financial_display_unit")
    st.caption(f"현재 표시 단위: {unit} | 원본 데이터와 재무지표 계산값은 변경되지 않습니다.")
    tab_bs, tab_is = st.tabs(["🏛️ 재무상태표 (BS)", "📈 손익계산서 (IS)"])
    with tab_bs:
        st.dataframe(_format_amount_table(df_bs, unit_options[unit]), use_container_width=True, hide_index=True)
    with tab_is:
        st.dataframe(_format_amount_table(df_is, unit_options[unit]), use_container_width=True, hide_index=True)