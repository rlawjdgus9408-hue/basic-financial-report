"""
Section 2: 자료 업로드
"""
import streamlit as st
import pandas as pd
import re
from pathlib import Path

_DEFAULT_TEMPLATE = Path(__file__).parent / "[그로스파이낸스]_기초재무진단결과_템플릿.docx"

def render_file_upload():
    """자료 업로드 렌더링"""
    st.markdown("### 3. 자료 업로드")
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.markdown("**재무진단 엑셀(RAW)**")
        uploaded_file = st.file_uploader("재무진단 엑셀 업로드", type=["xlsx"], label_visibility="collapsed")
    with col_up2:
        st.markdown("**워드 템플릿 (.docx)** — 기본 템플릿 자동 사용")
        custom_template = st.file_uploader("커스텀 템플릿으로 교체 (선택)", type=["docx"], label_visibility="collapsed")
        if custom_template:
            template_file = custom_template
        elif _DEFAULT_TEMPLATE.exists():
            template_file = str(_DEFAULT_TEMPLATE)
            st.caption(f"기본 템플릿 사용 중: {_DEFAULT_TEMPLATE.name}")
        else:
            template_file = None
            st.warning("기본 템플릿 파일을 찾을 수 없습니다. 템플릿을 직접 업로드해주세요.")
    
    df_bs = None
    df_is = None
    years = []
    
    if uploaded_file:
        try:
            df_raw_full = pd.read_excel(uploaded_file, sheet_name='RAW', engine='openpyxl', header=None)
            
            header_idx = -1
            year_cols_dict = {}
            for idx, row in df_raw_full.iterrows():
                found = {c: m.group(1) for c, v in enumerate(row) if (m := re.search(r'(20\d{2})', str(v)))}
                if len(found) >= 2:
                    header_idx, year_cols_dict = idx, found
                    break
            
            if header_idx != -1:
                years = list(year_cols_dict.values())
                
                def get_clean_data(source_df, start, end=None):
                    subset = source_df.iloc[start:end].copy()
                    name_col_end = min(year_cols_dict.keys())
                    name_data = subset.iloc[:, 0:name_col_end].fillna("").astype(str)
                    for col in name_data.columns:
                        name_data[col] = name_data[col].replace(['0', '0.0', 'nan', 'None'], '')
                    subset['계정과목'] = name_data.agg(" ".join, axis=1).str.strip()
                    y_names = list(year_cols_dict.values())
                    for c_idx, yr in year_cols_dict.items():
                        subset[yr] = pd.to_numeric(subset[c_idx], errors='coerce').fillna(0)
                    return subset[subset['계정과목'] != ""][['계정과목'] + y_names].reset_index(drop=True)
                
                is_start_row = -1
                for idx, row in df_raw_full.iterrows():
                    row_str = " ".join([str(v) for v in row if pd.notna(v)])
                    if "매출액" in row_str or "손익계산서" in row_str:
                        is_start_row = idx
                        break
                
                df_bs = get_clean_data(df_raw_full, header_idx + 1, is_start_row)
                df_is = get_clean_data(df_raw_full, is_start_row if is_start_row != -1 else header_idx + 1)
                
        except Exception as e:
            st.error(f"파일 파싱 오류: {e}")
    
    return uploaded_file, template_file, df_bs, df_is, years