"""
Section 2: 자료 업로드
"""
import streamlit as st
import pandas as pd
import re
import io
from pathlib import Path

_DEFAULT_TEMPLATE = Path(__file__).parent / "[그로스파이낸스]_기초재무진단결과_템플릿.docx"

@st.cache_data(show_spinner=False)
def _parse_raw_excel(file_bytes):
    """RAW 시트의 BS/IS 영역을 추출한다."""
    raw_df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="RAW", engine="openpyxl", header=None)

    header_idx = -1
    year_cols = {}
    for idx, row in raw_df.iterrows():
        found = {
            column: match.group(1)
            for column, value in enumerate(row)
            if (match := re.search(r"(20\d{2})", str(value)))
        }
        if len(found) >= 2:
            header_idx, year_cols = idx, found
            break
    if header_idx == -1:
        raise ValueError("연도 열을 두 개 이상 찾을 수 없습니다.")

    is_start_row = next(
        (
            idx
            for idx, row in raw_df.iterrows()
            if "매출액" in " ".join(str(value) for value in row if pd.notna(value))
            or "손익계산서" in " ".join(str(value) for value in row if pd.notna(value))
        ),
        -1,
    )
    if is_start_row <= header_idx:
        raise ValueError("손익계산서 시작 행을 찾을 수 없습니다.")

    def clean_data(start, end=None):
        subset = raw_df.iloc[start:end].copy()
        name_data = subset.iloc[:, :min(year_cols)].fillna("").astype(str)
        name_data = name_data.replace(["0", "0.0", "nan", "None"], "")
        subset["계정과목"] = name_data.agg(" ".join, axis=1).str.strip()
        year_names = list(year_cols.values())
        for column, year in year_cols.items():
            subset[year] = pd.to_numeric(subset[column], errors="coerce").fillna(0)
        return subset.loc[subset["계정과목"] != "", ["계정과목"] + year_names].reset_index(drop=True)

    return clean_data(header_idx + 1, is_start_row), clean_data(is_start_row), list(year_cols.values())


def render_file_upload():
    """자료 업로드 렌더링"""
    st.markdown("### 3. 자료 업로드")
    st.markdown("**재무진단 엑셀(RAW)**")
    uploaded_file = st.file_uploader("재무진단 엑셀 업로드", type=["xlsx"], label_visibility="collapsed")
    template_file = str(_DEFAULT_TEMPLATE) if _DEFAULT_TEMPLATE.exists() else None

    if not uploaded_file:
        return uploaded_file, template_file, None, None, []

    try:
        df_bs, df_is, years = _parse_raw_excel(uploaded_file.getvalue())
        return uploaded_file, template_file, df_bs, df_is, years
    except (OSError, ValueError, ImportError, KeyError) as error:
        st.error(f"파일 파싱 오류: {error}")
        return uploaded_file, template_file, None, None, []