"""
Section 2 보조: 다른 형식의 원본 파일(엑셀/PDF/스캔 이미지) -> 표준 RAW 형식 변환
"""
import io
import json

import pandas as pd
import streamlit as st

from sections.ai_client import configured_value, gemini_model

_MIME_BY_EXT = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "years": {"type": "array", "items": {"type": "string"}},
        "balance_sheet": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "values": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["account", "values"],
            },
        },
        "income_statement": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "values": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["account", "values"],
            },
        },
    },
    "required": ["years", "balance_sheet", "income_statement"],
}

_PROMPT = """당신은 한국 중소기업 재무제표 판독 전문가입니다.
첨부된 자료(재무상태표/손익계산서)에서 계정과목과 연도별 금액을 정확히 추출하세요.

규칙:
- 연도가 여러 개 있으면 전부 추출하고, years 배열은 오래된 연도 -> 최신 연도 순으로 정렬하세요.
- 금액은 원(KRW) 단위 정수로 변환하세요. "백만원", "천원" 등 단위가 표기돼 있으면 원 단위로 환산하세요.
- 계정과목명은 원문 표기를 그대로 유지하고, 임의로 통합·축약하지 마세요.
- 소계/합계 행("유동자산", "자산총계" 등)도 그대로 포함하세요.
- 값을 확인할 수 없는 계정은 0으로 채우지 말고 생략하세요.
- balance_sheet에는 재무상태표 계정만, income_statement에는 손익계산서 계정만 넣으세요.
"""


def _to_content_parts(file_bytes, filename):
    """업로드 파일을 Gemini에 보낼 contents 파츠로 변환한다."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in _MIME_BY_EXT:
        from google.genai import types
        return [types.Part.from_bytes(data=file_bytes, mime_type=_MIME_BY_EXT[ext])]

    if ext in ("xlsx", "xls"):
        sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)
        lines = []
        for sheet_name, df in sheets.items():
            lines.append(f"[시트: {sheet_name}]")
            lines.append(df.fillna("").astype(str).to_csv(sep="\t", index=False, header=False))
        return ["\n".join(lines)]

    raise ValueError(f"지원하지 않는 파일 형식입니다: .{ext}")


def _extract_financial_data(file_bytes, filename, api_key, model):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    contents = [_PROMPT] + _to_content_parts(file_bytes, filename)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_EXTRACTION_SCHEMA,
        ),
    )
    return json.loads(response.text)


def _to_dataframe(entries, years):
    rows = []
    for entry in entries:
        row = {"계정과목": str(entry.get("account", "")).strip()}
        for year, value in zip(years, entry.get("values", [])):
            row[year] = value
        rows.append(row)
    df = pd.DataFrame(rows, columns=["계정과목"] + list(years))
    for year in years:
        df[year] = pd.to_numeric(df[year], errors="coerce").fillna(0)
    return df


def render_raw_converter():
    """다른 형식 파일을 업로드하면 AI로 표준 RAW 형식으로 변환하고, 결과를 검토/수정할 수 있게 한다."""
    st.caption(
        "엑셀(다른 양식), PDF, 스캔 이미지를 업로드하면 AI가 재무상태표/손익계산서를 표준 형식으로 변환합니다. "
        "변환 결과는 반드시 아래 표에서 직접 검토·수정한 뒤 다음 단계로 진행하세요."
    )

    converter_file = st.file_uploader(
        "원본 재무제표 파일 업로드 (엑셀/PDF/이미지)",
        type=["xlsx", "xls", "pdf", "png", "jpg", "jpeg"],
        key="convert_source_file",
    )

    if converter_file is None:
        st.session_state.pop("convert_result_key", None)
        return None, None, None, []

    file_key = f"{converter_file.name}:{converter_file.size}"

    if st.session_state.get("convert_result_key") != file_key:
        configured_key = configured_value("Gemini", "api_key")
        if configured_key:
            api_key = configured_key
            st.caption("Gemini API 키가 로컬 보안 설정에서 로드되었습니다.")
        else:
            api_key = st.text_input(
                "Gemini API 키 (환경변수 또는 Streamlit secrets 설정 시 생략 가능)",
                type="password",
                key="convert_api_key",
            ).strip()

        if st.button("AI로 변환하기", type="primary", key="convert_run_btn"):
            if not api_key:
                st.error("Gemini API 키를 입력하거나 환경변수/Streamlit secrets에 설정해주세요.")
                return converter_file, None, None, []
            try:
                with st.spinner("파일을 분석하여 표준 형식으로 변환하고 있습니다..."):
                    data = _extract_financial_data(
                        converter_file.getvalue(), converter_file.name, api_key, gemini_model()
                    )
                years = data.get("years", [])
                if not years:
                    st.error("연도 정보를 인식하지 못했습니다. 파일을 확인하고 다시 시도해주세요.")
                    return converter_file, None, None, []
                st.session_state["convert_df_bs"] = _to_dataframe(data.get("balance_sheet", []), years)
                st.session_state["convert_df_is"] = _to_dataframe(data.get("income_statement", []), years)
                st.session_state["convert_years"] = years
                st.session_state["convert_result_key"] = file_key
                st.rerun()
            except (ValueError, json.JSONDecodeError) as error:
                st.error(f"변환에 실패했습니다: {error}")
            except Exception as error:
                st.error(f"AI 변환 중 오류가 발생했습니다: {error}")
        return converter_file, None, None, []

    st.success("변환 완료 — 아래 표에서 값을 확인하고 필요하면 직접 수정한 뒤 진행하세요.")
    tab_bs, tab_is = st.tabs(["재무상태표 (BS)", "손익계산서 (IS)"])
    with tab_bs:
        edited_bs = st.data_editor(
            st.session_state["convert_df_bs"], use_container_width=True, num_rows="dynamic", key="convert_bs_editor"
        )
    with tab_is:
        edited_is = st.data_editor(
            st.session_state["convert_df_is"], use_container_width=True, num_rows="dynamic", key="convert_is_editor"
        )

    if st.button("다른 파일로 다시 변환하기", key="convert_reset_btn"):
        st.session_state.pop("convert_result_key", None)
        st.rerun()

    return converter_file, edited_bs, edited_is, st.session_state["convert_years"]
