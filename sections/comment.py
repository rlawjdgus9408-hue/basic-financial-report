"""
Section 5: 종합의견
"""
import json
import os
import re
from pathlib import Path

import streamlit as st
import pandas as pd

_CONFIG_FILE = Path(__file__).parent.parent / "config.json"
_USER_ICON = Path(__file__).parent.parent / "assets" / "icons" / "assistant_icon.webp"
_GEMINI_ICON = Path(__file__).parent.parent / "assets" / "icons" / "gemini_icon.svg"
_DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


def _configured_value(provider, key):
    env_name = "GEMINI_API_KEY"
    if key == "api_key":
        try:
            secret_value = st.secrets.get(env_name, "")
        except Exception:
            secret_value = ""
        return secret_value or os.getenv(env_name, "")

    try:
        config = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        for model_config in config.get("models", []):
            if model_config.get("provider", "").lower() == provider.lower():
                return model_config.get(key, model_config.get("apiKey", "") if key == "api_key" else "")
    except (OSError, json.JSONDecodeError):
        pass
    return ""


def _gemini_model():
    configured_model = _configured_value("Gemini", "model")
    if configured_model in {"", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-flash"}:
        return _DEFAULT_GEMINI_MODEL
    return configured_model


def _financial_context():
    context = {
        "기업명": st.session_state.get("input_co_name", ""),
        "업종": st.session_state.get("input_biz_minor", "") or st.session_state.get("input_biz_direct", ""),
        "선택 지표": st.session_state.get("selected_indicators", {}),
        "재무상태표 지표": st.session_state.get("bs_metrics", {}),
        "손익계산서 지표": st.session_state.get("is_metrics", {}),
        "공통 지표": st.session_state.get("common_metrics", {}),
    }
    return json.dumps(context, ensure_ascii=False, default=str)


def _has_financial_data():
    return any(
        st.session_state.get(key)
        for key in ("bs_metrics", "is_metrics", "common_metrics")
    )


def _plain_text_ai_answer(answer):
    """AI Markdown 답변을 종합의견용 일반 텍스트로 정리한다."""
    answer = re.sub(r"\*\*(.*?)\*\*", r"\1", answer, flags=re.DOTALL)
    answer = answer.replace("**", "").replace("__", "").replace("`", "")
    answer = re.sub(r"(?m)^\s*#{1,6}\s*", "", answer)
    return answer.strip()


def _generate_ai_response(provider, model, api_key, question):
    prompt = f"""당신은 중소기업 재무분석 전문가입니다.
아래 기업 데이터를 근거로 질문에 한국어로 답변하세요.
수치가 없는 내용은 추정하지 말고, 답변은 실무자가 바로 활용할 수 있게 작성하세요.

[기업 데이터]
{_financial_context()}

[질문]
{question}
"""

    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text or "응답을 받지 못했습니다."


def render_ai_comment_chat():
    with st.expander("AI 재무 분석 코멘트", expanded=False):
        with st.container(height=620, border=True):
            if not _has_financial_data():
                st.info("재무 엑셀을 업로드하면 재무지표를 바탕으로 더 정확한 분석을 받을 수 있습니다.")

            model = _gemini_model()
            configured_key = _configured_value("Gemini", "api_key")
            if configured_key:
                api_key = configured_key
                st.caption("Gemini API 키가 로컬 보안 설정에서 로드되었습니다.")
            else:
                api_key = st.text_input(
                    "Gemini API 키 (환경변수 또는 Streamlit secrets 설정 시 생략 가능)",
                    type="password",
                    key="ai_key_gemini",
                ).strip()

            messages = st.session_state.setdefault("ai_messages", [])
            for message in messages:
                avatar = str(_GEMINI_ICON) if message["role"] == "assistant" else str(_USER_ICON)
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])
                    if message["role"] == "assistant":
                        st.markdown(
                            f'<div class="ai-model-label">{model}</div>',
                            unsafe_allow_html=True,
                        )

            with st.form("ai_question_form", clear_on_submit=True):
                question = st.text_input("질문", placeholder="재무 상태에 대해 질문하세요")
                submitted = st.form_submit_button("질문하기", type="primary")

            if submitted and question.strip():
                question = question.strip()
                messages.append({"role": "user", "content": question})
                if not api_key:
                    answer = "Gemini API 키를 입력하거나 환경변수/Streamlit secrets에 설정해주세요."
                else:
                    try:
                        with st.spinner("재무 데이터를 분석하고 있습니다..."):
                            answer = _generate_ai_response("Gemini", model, api_key, question)
                    except Exception as error:
                        answer = f"AI 응답을 생성하지 못했습니다: {error}"
                messages.append({"role": "assistant", "content": answer})
                st.rerun()

            if messages:
                if st.button("마지막 AI 답변을 종합의견에 반영", key="apply_ai_comment"):
                    last_answer = next(
                        (message["content"] for message in reversed(messages) if message["role"] == "assistant"),
                        "",
                    )
                    if last_answer:
                        st.session_state["txt_exec"] = _plain_text_ai_answer(last_answer)
                        st.rerun()


def render_comments():
    """종합의견 렌더링"""
    st.markdown("### 5. 종합의견")

    # 선택된 지표 기반 표 표시
    selected_indicators = st.session_state.get('selected_indicators', {})
    if selected_indicators and any(selected_indicators.get(k) for k in ('bs', 'is', 'common')):
        st.markdown("#### 문서 포함 선택된 재무지표")

        years       = st.session_state.get('years', [])
        bs_metrics  = st.session_state.get('bs_metrics', {})
        is_metrics  = st.session_state.get('is_metrics', {})
        common_metrics = st.session_state.get('common_metrics', {})

        all_selected = (selected_indicators.get('bs', [])
                        + selected_indicators.get('is', [])
                        + selected_indicators.get('common', []))

        if all_selected and years:
            table_data = []
            for ind in all_selected:
                row = {'지표명': ind}
                for yr in years:
                    val = next(
                        (m[yr][ind] for m in (bs_metrics, is_metrics, common_metrics)
                         if m.get(yr) and ind in m[yr]),
                        None
                    )
                    row[yr] = f"{val:,.2f}" if val is not None else "-"
                table_data.append(row)

            df_selected = pd.DataFrame(table_data)
            st.dataframe(df_selected.set_index('지표명'), use_container_width=True)
            st.caption("※ 문서 포함을 선택한 지표입니다.")

            # 템플릿용 표 문자열 생성 및 세션 저장
            lines = ["■ 주요 재무지표", "지표명\t" + "\t".join(years)]
            for row in table_data:
                lines.append(row['지표명'] + "".join(f"\t{row.get(yr,'-')}" for yr in years))
            st.session_state.selected_indicators_table = "\n".join(lines)


    render_ai_comment_chat()

    # 글머리 자동 추가: 위젯 렌더링 전에 session_state 값을 미리 처리
    _current = st.session_state.get('txt_exec', st.session_state.get('exec_summary', ''))
    if _current:
        lines = []
        for line in _current.split('\n'):
            stripped = line.strip()
            lines.append(('▪ ' + stripped) if stripped and not stripped.startswith('▪') else line)
        _bulleted = '\n'.join(lines)
        if _bulleted != _current:
            st.session_state['txt_exec'] = _bulleted

    exec_summary = st.text_area(
        "종합의견 (Executive Summary)",
        value=st.session_state.get('exec_summary', ''),
        height=200,
        key="txt_exec",
        help="입력 후 커서를 벗어나면 각 문단 앞에 ▪ 글머리가 자동으로 추가됩니다."
    )

    char_count = len(exec_summary) if exec_summary else 0
    st.caption(f"글자수: {char_count}/2000자  |  커서 이동 시 ▪ 글머리 자동 추가")
    if char_count > 2000:
        st.warning("A4 1장 기준(2000자)을 초과했습니다.")

    return exec_summary
