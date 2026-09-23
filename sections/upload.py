"""
Section 2: 자료 업로드
"""
import streamlit as st
import pandas as pd
import re
import io
from pathlib import Path

from sections.convert import render_raw_converter

_DEFAULT_TEMPLATE = Path(__file__).parent.parent / "assets" / "templates" / "[그로스파이낸스]_기초재무진단결과_템플릿.docx"

@st.cache_data(show_spinner=False)
def _parse_raw_excel(file_bytes):
    """RAW 시트의 BS/IS 영역을 추출한다.

    RAW 시트는 재무상태표 -> 손익계산서 -> (있다면) 제조원가명세서/이익잉여금처분계산서 등
    순서로 섹션이 이어진다(build_raw.py, raw_template.py 모두 이 구조로 생성). 각 섹션은
    "제목행" 바로 다음 줄에 연도가 2개 이상 나열된 "계정과목/연도" 헤더행이 오므로, 그런
    헤더행을 전부 순서대로 찾아두면 그 사이 구간이 곧 각 섹션의 데이터 범위가 된다.
    (이렇게 하지 않고 "손익계산서는 그 다음부터 시트 끝까지"로 잡으면, 손익계산서 뒤에
    다른 섹션이 더 있는 RAW 시트에서 그 섹션 전체가 손익계산서 데이터에 섞여 들어간다.)
    """
    raw_df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="RAW", engine="openpyxl", header=None)

    header_rows = []
    year_cols = {}
    for idx, row in raw_df.iterrows():
        found = {
            column: match.group(1)
            for column, value in enumerate(row)
            if (match := re.search(r"(20\d{2})", str(value)))
        }
        if len(found) >= 2:
            header_rows.append(idx)
            if not year_cols:
                year_cols = found

    if not header_rows:
        raise ValueError("연도 열을 두 개 이상 찾을 수 없습니다.")
    if len(header_rows) < 2:
        raise ValueError("손익계산서 시작 행을 찾을 수 없습니다.")

    bs_header_idx, is_header_idx = header_rows[0], header_rows[1]
    # 손익계산서 다음에 다른 섹션이 더 있으면, 그 섹션의 제목행(=자기 헤더행 바로 위)에서
    # 손익계산서 구간을 끊는다. 더 없으면 시트 끝까지가 손익계산서 구간이다.
    next_header_idx = header_rows[2] if len(header_rows) > 2 else None
    is_end_row = (next_header_idx - 1) if next_header_idx is not None else None
    bs_end_row = is_header_idx - 1  # 손익계산서 제목행 직전까지가 재무상태표 구간

    def clean_data(start, end=None):
        subset = raw_df.iloc[start:end].copy()
        name_data = subset.iloc[:, :min(year_cols)].fillna("").astype(str)
        name_data = name_data.replace(["0", "0.0", "nan", "None"], "")
        subset["계정과목"] = name_data.agg(" ".join, axis=1).str.strip()
        year_names = list(year_cols.values())
        for column, year in year_cols.items():
            subset[year] = pd.to_numeric(subset[column], errors="coerce").fillna(0)
        return subset.loc[subset["계정과목"] != "", ["계정과목"] + year_names].reset_index(drop=True)

    return (
        clean_data(bs_header_idx + 1, bs_end_row),
        clean_data(is_header_idx + 1, is_end_row),
        list(year_cols.values()),
    )


def render_file_upload():
    """자료 업로드 렌더링"""
    st.markdown("### 3. 자료 업로드")
    template_file = str(_DEFAULT_TEMPLATE) if _DEFAULT_TEMPLATE.exists() else None

    mode = st.radio(
        "업로드 방식",
        ["표준 RAW 엑셀", "다른 형식 파일 변환 (AI)"],
        horizontal=True,
        key="upload_mode",
    )

    if mode == "다른 형식 파일 변환 (AI)":
        uploaded_file, df_bs, df_is, years = render_raw_converter()
        return uploaded_file, template_file, df_bs, df_is, years

    st.markdown("**재무진단 엑셀(RAW)**")
    uploaded_file = st.file_uploader("재무진단 엑셀 업로드", type=["xlsx"], label_visibility="collapsed")

    if not uploaded_file:
        return uploaded_file, template_file, None, None, []

    try:
        df_bs, df_is, years = _parse_raw_excel(uploaded_file.getvalue())
        return uploaded_file, template_file, df_bs, df_is, years
    except (OSError, ValueError, ImportError, KeyError) as error:
        st.error(f"파일 파싱 오류: {error}")
        return uploaded_file, template_file, None, None, []