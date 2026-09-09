"""
Section 2 보조: 다른 형식의 원본 파일(엑셀/PDF/스캔 이미지) -> 표준 RAW 형식 변환

원본 재무제표(국세청 표준재무제표증명, 스캔본, 감사보고서/자체결산서 등)를 업로드하면
AI가 재무상태표/손익계산서를 추출한다. 기존 RAW 엑셀이 있으면 새 연도 컬럼을 이어붙이고,
없으면 새 RAW 엑셀을 만든다. 두 경우 모두 결과를 표로 보여주고 사용자가 검토/수정한 뒤에만
반영한다.
"""
import io
import json

import pandas as pd
import streamlit as st

from sections.ai_client import configured_value, gemini_model
from sections import raw_template

_MIME_BY_EXT = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

_ACCOUNT_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "account": {"type": "string"},
        "code": {"type": "string", "nullable": True},
        "values": {"type": "array", "items": {"type": "number"}},
    },
    "required": ["account", "values"],
}

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "years": {"type": "array", "items": {"type": "string"}},
        "balance_sheet": {"type": "array", "items": _ACCOUNT_ENTRY_SCHEMA},
        "income_statement": {"type": "array", "items": _ACCOUNT_ENTRY_SCHEMA},
    },
    "required": ["years", "balance_sheet", "income_statement"],
}

_PROMPT = """당신은 한국 중소기업 재무제표 판독 전문가입니다.
첨부된 자료(재무상태표/손익계산서)에서 계정과목과 연도별 금액을 정확히 추출하세요.

규칙:
- 국세청 표준재무제표증명처럼 계정과목 옆에 "코드" 번호가 함께 인쇄돼 있으면 code 필드에 그
  번호를 그대로 적으세요. 코드가 없는 자유형식 문서(감사보고서, 자체결산서 등)는 code를 생략하거나
  null로 두세요.
- 표준재무제표증명에는 업종에 맞지 않는 빈 서식(예: 금융·보험·증권업용 표에 값이 전혀 없는 경우)이
  함께 첨부되기도 합니다. 값이 있는 서식만 사용하고 빈 서식은 무시하세요.
- 연도가 여러 개 있으면 전부 추출하고, years 배열은 오래된 연도 -> 최신 연도 순으로 정렬하세요.
- 금액은 원(KRW) 단위 정수로 변환하세요. "백만원", "천원" 등 단위가 표기돼 있으면 원 단위로 환산하세요.
- 계정과목명은 원문 표기를 그대로 유지하고, 임의로 통합·축약하지 마세요.
- 소계/합계 행("유동자산", "자산총계" 등)도 원본에 그 값이 명시돼 있다면 그대로 포함하세요.
- 값을 확인할 수 없는 계정은 0으로 채우지 말고 생략하세요.
- balance_sheet에는 재무상태표 계정만, income_statement에는 손익계산서 계정만 넣으세요.
- 출력하기 전에 자체 검산하세요: "자산총계=유동자산+비유동자산", "부채총계=유동부채+비유동부채",
  "자본총계=부채와자본총계-부채총계" 처럼 총계/소계 행은 그 하위 항목 합과 반드시 일치해야 합니다.
  숫자를 잘못 읽어 합이 맞지 않으면 원본을 다시 확인해 금액을 바로잡으세요.
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


def _slice_entries_for_year(entries, all_years, year):
    """여러 연도가 섞인 추출 결과에서 특정 연도 값만 뽑아 단일 연도 entries로 만든다."""
    idx = all_years.index(year)
    sliced = []
    for entry in entries:
        values = entry.get("values", [])
        if idx < len(values):
            sliced.append({"account": entry.get("account", ""), "values": [values[idx]]})
    return sliced


def _run_conversion(source_file, existing_file):
    """AI 추출 + (있으면) 기존 RAW와 병합해 세션 상태에 검토용 결과를 저장한다."""
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

    if not st.button("AI로 변환하기", type="primary", key="convert_run_btn"):
        return
    if not api_key:
        st.error("Gemini API 키를 입력하거나 환경변수/Streamlit secrets에 설정해주세요.")
        return

    try:
        with st.spinner("파일을 분석하여 표준 형식으로 변환하고 있습니다..."):
            data = _extract_financial_data(source_file.getvalue(), source_file.name, api_key, gemini_model())
        src_years = data.get("years", [])
        if not src_years:
            st.error("연도 정보를 인식하지 못했습니다. 파일을 확인하고 다시 시도해주세요.")
            return

        if existing_file is not None:
            existing_bytes = existing_file.getvalue()
            existing = raw_template.read_existing_raw(existing_bytes)
            new_year = src_years[-1]
            bs_year_entries = _slice_entries_for_year(data.get("balance_sheet", []), src_years, new_year)
            is_year_entries = _slice_entries_for_year(data.get("income_statement", []), src_years, new_year)
            bs_plan = raw_template.auto_match(existing["bs_rows"], bs_year_entries)
            is_plan = raw_template.auto_match(existing["is_rows"], is_year_entries)
            years = list(existing["years"])
            if new_year not in years:
                years.append(new_year)

            st.session_state["convert_mode"] = "merge"
            st.session_state["convert_existing_bytes"] = existing_bytes
            st.session_state["convert_existing_meta"] = existing
            st.session_state["convert_new_year"] = new_year
            st.session_state["convert_df_bs"] = pd.DataFrame(raw_template.preview_to_dataframe_records(bs_plan, years))
            st.session_state["convert_df_is"] = pd.DataFrame(raw_template.preview_to_dataframe_records(is_plan, years))
        else:
            st.session_state["convert_mode"] = "new"
            st.session_state["convert_df_bs"] = _to_dataframe(data.get("balance_sheet", []), src_years)
            st.session_state["convert_df_is"] = _to_dataframe(data.get("income_statement", []), src_years)
            years = src_years

        st.session_state["convert_years"] = years
        st.session_state["convert_result_key"] = _file_key(source_file, existing_file)
        st.rerun()
    except (ValueError, json.JSONDecodeError) as error:
        st.error(f"변환에 실패했습니다: {error}")
    except Exception as error:
        st.error(f"AI 변환 중 오류가 발생했습니다: {error}")


def _file_key(source_file, existing_file):
    src = f"{source_file.name}:{source_file.size}"
    existing = f"{existing_file.name}:{existing_file.size}" if existing_file is not None else "none"
    return f"{src}|{existing}"


def _build_download(edited_bs, edited_is):
    """검토 표(수정 반영)를 기반으로 최종 RAW 엑셀 bytes를 만든다."""
    years = st.session_state["convert_years"]
    if st.session_state.get("convert_mode") == "merge":
        existing = st.session_state["convert_existing_meta"]
        bs_plan = raw_template.plan_from_edited(existing["bs_rows"], edited_bs.to_dict("records"), years)
        is_plan = raw_template.plan_from_edited(existing["is_rows"], edited_is.to_dict("records"), years)
        file_bytes, unmatched = raw_template.write_merged_workbook(
            st.session_state["convert_existing_bytes"], existing, bs_plan, is_plan, st.session_state["convert_new_year"]
        )
        return file_bytes, unmatched

    bs_entries = raw_template.entries_from_records(edited_bs.to_dict("records"), years)
    is_entries = raw_template.entries_from_records(edited_is.to_dict("records"), years)
    return raw_template.write_new_raw_workbook(bs_entries, is_entries, years), []


def render_raw_converter():
    """원본 파일을 업로드하면 AI로 표준 RAW 형식으로 변환하고, 결과를 검토/수정할 수 있게 한다."""
    st.caption(
        "국세청 표준재무제표증명, 스캔본, 감사보고서/자체결산서 등을 업로드하면 AI가 재무상태표/손익계산서를 "
        "표준 형식으로 변환합니다. 변환 결과는 반드시 아래 표에서 직접 검토·수정한 뒤 다음 단계로 진행하세요."
    )

    existing_file = st.file_uploader(
        "기존 RAW 엑셀 파일 (선택 — 있으면 새 연도를 자동으로 이어붙입니다)",
        type=["xlsx"],
        key="convert_existing_raw_file",
    )
    source_file = st.file_uploader(
        "원본 재무제표 파일 업로드 (엑셀/PDF/이미지)",
        type=["xlsx", "xls", "pdf", "png", "jpg", "jpeg"],
        key="convert_source_file",
    )

    if source_file is None:
        st.session_state.pop("convert_result_key", None)
        return None, None, None, []

    file_key = _file_key(source_file, existing_file)

    if st.session_state.get("convert_result_key") != file_key:
        _run_conversion(source_file, existing_file)
        return source_file, None, None, []

    years = st.session_state["convert_years"]
    st.success("변환 완료 — 아래 표에서 값을 확인하고 필요하면 직접 수정한 뒤 진행하세요.")
    if st.session_state.get("convert_mode") == "merge":
        st.caption(f"기존 RAW 파일의 {', '.join(existing_yr for existing_yr in years[:-1])}년 데이터에 {years[-1]}년 컬럼을 추가합니다.")

    tab_bs, tab_is = st.tabs(["재무상태표 (BS)", "손익계산서 (IS)"])
    with tab_bs:
        edited_bs = st.data_editor(
            st.session_state["convert_df_bs"], use_container_width=True, num_rows="dynamic", key="convert_bs_editor"
        )
    with tab_is:
        edited_is = st.data_editor(
            st.session_state["convert_df_is"], use_container_width=True, num_rows="dynamic", key="convert_is_editor"
        )

    col_reset, col_download = st.columns([1, 1])
    with col_reset:
        if st.button("다른 파일로 다시 변환하기", key="convert_reset_btn", use_container_width=True):
            st.session_state.pop("convert_result_key", None)
            st.rerun()
    with col_download:
        try:
            file_bytes, unmatched = _build_download(edited_bs, edited_is)
            company = st.session_state.get("input_co_name") or "진단기업"
            st.download_button(
                "RAW 엑셀 다운로드",
                data=file_bytes,
                file_name=f"{company}_RAW_{years[-1]}.xlsx",
                use_container_width=True,
                key="convert_download_btn",
            )
            if unmatched:
                st.caption(
                    "⚠ 기존 시트에 없던 계정 " + ", ".join(unmatched) + " 은(는) 각 표 맨 끝에 "
                    "'미분류 신규 계정'으로 추가했습니다 — 총계/합계 범위에 포함되도록 엑셀에서 직접 확인해주세요."
                )
        except Exception as error:
            st.error(f"엑셀 파일 생성 중 오류가 발생했습니다: {error}")

    return source_file, edited_bs, edited_is, years
