"""
Section 5: 종합의견
"""
import streamlit as st
import pandas as pd


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
