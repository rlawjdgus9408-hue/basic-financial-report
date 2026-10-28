"""
Section 3-1: 재무지표 연도별 추이
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# ── 공통 설정 ────────────────────────────────────────────────────────────────
_CHART_CONFIG = {
    'toImageButtonOptions': {'format': 'png', 'filename': 'chart', 'height': 500, 'width': 800, 'scale': 2},
    'displayModeBar': True,
    'displaylogo': False,
}

# 그래프는 페이지가 검정이어도 흰 배경 카드로 표시한다 — 화면 가독성뿐 아니라, PNG
# 다운로드(툴바의 카메라 아이콘) 결과물도 이 배경을 그대로 따라가기 때문에 검정 배경으로
# 두면 다운로드한 이미지가 보기/인쇄하기 어려워진다.
_CHART_LAYOUT = dict(
    template='plotly_white',
    paper_bgcolor='#FFFFFF',
    plot_bgcolor='#FFFFFF',
    font=dict(color='#191919'),
)

# 범례별 색상 구분용 고정 팔레트. Plotly Express의 자동 색상은 .streamlit/config.toml의
# 다크 테마(매우 어두운 backgroundColor)를 기반으로 생성되는데, 이 조합에서 Streamlit이
# 만들어내는 자동 팔레트가 전부 거의 검정(#000001, #000002, ...)으로 뭉개지는 문제가 있다 —
# 화면 테마와 무관해야 할 PNG 차트(보고서 삽입용)까지 그 영향을 받는다. 색맹 안전성까지
# 검증된 고정 순서 팔레트를 명시적으로 지정해 테마 상태에 의존하지 않게 한다.
_CATEGORICAL_COLORS = [
    '#2a78d6', '#eb6834', '#1baf7a', '#eda100',
    '#e87ba4', '#008300', '#4a3aa7', '#e34948',
]

BS_INDICATORS = [
    '유동비율', '당좌비율', '현금비율', '부채비율', '자기자본비율',
    '유동부채비율', '비유동자산비율', '재고자산비율',
    '매출채권회전율', '재고자산회전율', '총자산회전율',
    '총자산증가율', '차입금의존도',
    '매출채권회수기간', '재고자산회전일수', '매입채무결제기간', '현금전환주기',
]
IS_INDICATORS = [
    '매출총이익률', '판매관리비율', '영업이익률', '순이익률', '매출원가율',
    'EBITDA마진', '비용구조비율',
    '매출액증가율', '총이익증가율', '영업이익증가율', '순이익증가율',
]
COMMON_INDICATORS = [
    'ROA', 'ROE', 'ROIC', 'EPS',
    '부채대비현금비율', '이자보상배율', '자본회전율',
    '자산대비영업이익률', '자본대비영업이익률',
]

# "지표 조합 그래프"에서 매번 30여 개 중 직접 고르지 않아도 되도록, 재무분석 목적별로
# 자주 함께 보는 지표를 미리 묶어둔 추천 조합. BS/IS/공통 출처 구분과는 달리 "무엇을
# 확인하려는가" 기준으로 묶는다.
RECOMMENDED_COMBOS = {
    "수익성 (얼마나 남기나)":      ['매출총이익률', '영업이익률', '순이익률', 'ROE'],
    "안정성 (재무구조가 튼튼한가)":  ['유동비율', '부채비율', '자기자본비율', '이자보상배율'],
    "활동성 (자산을 잘 굴리나)":    ['매출채권회전율', '재고자산회전율', '총자산회전율'],
    "성장성 (외형이 커지고 있나)":  ['매출액증가율', '영업이익증가율', '순이익증가율'],
    "자본수익성 (투자 대비 성과)":  ['ROA', 'ROE', 'ROIC'],
}


def find_account(df, keywords, years):
    """계정 검색 — 연도별 값 딕셔너리 반환.

    일부 RAW 파일은 본문 계정과 별도로 "영업이익률", "매출액증가율(%)" 같은 비율 요약 행을
    같은 표 안에 함께 담고 있다. 이런 행이 "영업이익" 같은 금액 키워드에 우연히 걸려
    (예: "영업이익률"이 "영업이익"을 포함) 금액 대신 비율값(예: 0.097)이 잘못 쓰이는 사고가
    실제로 있었다 — 라벨에 "률"이나 "%"가 있으면 애초에 매칭 대상에서 제외한다."""
    for kw in keywords:
        matches = df[
            df['계정과목'].str.contains(kw, case=False, na=False)
            & ~df['계정과목'].str.contains('률|%', case=False, na=False)
        ]
        if not matches.empty:
            row = matches.iloc[0]
            result = {}
            for yr in years:
                if yr in row.index:
                    try:
                        result[yr] = float(row[yr]) if pd.notna(row[yr]) else 0
                    except (ValueError, TypeError):
                        result[yr] = 0
            return result
    return None


_BORROWING_GROUPS = [
    # (이 묶음에 해당하는 계정 패턴, 제외 패턴)
    ('단기차입금', None),
    ('장기차입금', '유동성'),
    ('유동성장기', None),
    ('사채', '할인|상환할증'),
]


def sum_borrowings(df, years):
    """총차입금(단기차입금 + 장기차입금 + 유동성장기부채 + 사채)의 연도별 합계.

    재무제표는 "2.단기차입금" 아래에 "다.기타단기차입금" 같은 세부 행을 함께 싣기 때문에, 패턴에
    걸리는 행을 전부 더하면 상위·세부 행이 이중으로 잡힌다. 묶음별로 처음 나오는 행(재무제표 순서상
    상위 행)만 쓴다. "차입금/자본총계" 같은 비율 행(률·%·/)과 이자 계정은 뺀다. 하나도 없으면 None."""
    labels = df['계정과목'].astype(str)
    usable = ~labels.str.contains('률|%|/|이자', na=False)
    rows = []
    for pattern, exclude in _BORROWING_GROUPS:
        hit = usable & labels.str.contains(pattern, na=False)
        if exclude:
            hit &= ~labels.str.contains(exclude, na=False)
        if hit.any():
            rows.append(df[hit].iloc[0])
    if not rows:
        return None
    return {
        yr: float(sum(pd.to_numeric(r.get(yr), errors='coerce') or 0 for r in rows))
        for yr in years
    }


def _get_metric_val(indicator, yr, bs_metrics, is_metrics, common_metrics):
    """세 지표 딕셔너리에서 값 탐색"""
    for m in (bs_metrics, is_metrics, common_metrics):
        if m.get(yr) and indicator in m[yr]:
            return m[yr][indicator]
    return None


def _metrics_df(metrics, indicators, years):
    """지표 딕셔너리 → 표시용 DataFrame"""
    df = pd.DataFrame(index=indicators, columns=years)
    for yr in years:
        for ind in indicators:
            val = metrics.get(yr, {}).get(ind)
            if val is not None:
                df.loc[ind, yr] = val
    return df.astype(str).replace({'nan': '-', 'None': '-'})


def _indicator_buttons(prefix, indicators, columns=4):
    selected = []
    cols = st.columns(columns)
    for i, indicator in enumerate(indicators):
        state_key = f"doc_{prefix}_{indicator}"
        is_selected = st.session_state.get(state_key, False)
        with cols[i % columns]:
            if st.button(
                indicator,
                key=f"indicator_btn_{prefix}_{indicator}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state[state_key] = not is_selected
                st.rerun()
        if is_selected:
            selected.append(indicator)
    return selected


# ── 지표 계산 ────────────────────────────────────────────────────────────────

def calculate_bs_metrics(bs_accounts, is_accounts, years):
    metrics = {}
    for yr in years:
        m = {}
        ca   = bs_accounts.get('유동자산') or {}
        cl   = bs_accounts.get('유동부채') or {}
        inv  = bs_accounts.get('재고자산') or {}
        cash = bs_accounts.get('현금및현금성자산') or {}
        liab = bs_accounts.get('부채총계') or {}
        eq   = bs_accounts.get('자본총계') or {}
        tot_ast = bs_accounts.get('자산총계') or {}
        nca  = bs_accounts.get('비유동자산') or {}
        ar   = bs_accounts.get('매출채권') or {}
        rev  = is_accounts.get('매출액') or {}
        cogs = is_accounts.get('매출원가') or {}

        cl_v    = cl.get(yr, 0)
        ca_v    = ca.get(yr, 0)
        eq_v    = eq.get(yr, 0)
        ast_v   = tot_ast.get(yr, 0)

        if ca and cl and cl_v:
            m['유동비율']    = round(ca_v / cl_v * 100, 2)
            m['당좌비율']    = round((ca_v - inv.get(yr, 0)) / cl_v * 100, 2)
            m['유동부채비율'] = round(cl_v / ca_v * 100, 2) if ca_v else None
        if cash and cl and cl_v:
            m['현금비율']    = round(cash.get(yr, 0) / cl_v * 100, 2)
        if eq and eq_v:
            m['부채비율']    = round(liab.get(yr, 0) / eq_v * 100, 2)
        if tot_ast and ast_v:
            m['자기자본비율']   = round(eq_v / ast_v * 100, 2)
            m['비유동자산비율'] = round(nca.get(yr, 0) / ast_v * 100, 2) if nca else None
        if inv and ca_v:
            m['재고자산비율'] = round(inv.get(yr, 0) / ca_v * 100, 2)
        if ar and rev and ar.get(yr, 0):
            m['매출채권회전율'] = round(rev.get(yr, 0) / ar.get(yr, 0), 2)
        if inv and cogs and inv.get(yr, 0):
            m['재고자산회전율'] = round(cogs.get(yr, 0) / inv.get(yr, 0), 2)
        if rev and tot_ast and ast_v:
            m['총자산회전율'] = round(rev.get(yr, 0) / ast_v, 2)

        borrow = bs_accounts.get('차입금') or {}
        if borrow and ast_v:
            m['차입금의존도'] = round(borrow.get(yr, 0) / ast_v * 100, 2)

        idx = years.index(yr)
        if idx > 0 and tot_ast:
            prev_ast = tot_ast.get(years[idx - 1], 0)
            if prev_ast:
                m['총자산증가율'] = round((ast_v - prev_ast) / abs(prev_ast) * 100, 2)

        # 활동성(일수) 지표는 스킬 Q4-1에 따라 기말 잔액 기준 하나로 통일한다(평균 잔액 혼용 금지).
        ap = bs_accounts.get('매입채무') or {}
        rev_v, cogs_v = rev.get(yr, 0), cogs.get(yr, 0)
        dso = round(ar.get(yr, 0) * 365 / rev_v, 1) if ar and rev_v else None
        dio = round(inv.get(yr, 0) * 365 / cogs_v, 1) if inv and cogs_v else None
        dpo = round(ap.get(yr, 0) * 365 / cogs_v, 1) if ap and cogs_v else None
        m['매출채권회수기간'] = dso
        m['재고자산회전일수'] = dio
        m['매입채무결제기간'] = dpo
        if None not in (dso, dio, dpo):
            m['현금전환주기'] = round(dso + dio - dpo, 1)

        metrics[yr] = {k: v for k, v in m.items() if v is not None}
    return metrics


def calculate_is_metrics(is_accounts, years):
    metrics = {}
    for yr in years:
        m = {}
        rev   = is_accounts.get('매출액') or {}
        cogs  = is_accounts.get('매출원가') or {}
        gross = is_accounts.get('매출총이익') or {}
        op    = is_accounts.get('영업이익') or {}
        ebitda = is_accounts.get('EBITDA') or {}
        net   = is_accounts.get('당기순이익') or {}
        sga   = is_accounts.get('판매관리비') or {}
        rev_v = rev.get(yr, 0)

        if rev_v:
            if gross: m['매출총이익률'] = round(gross.get(yr, 0) / rev_v * 100, 2)
            if sga:   m['판매관리비율'] = round(sga.get(yr, 0)   / rev_v * 100, 2)
            if op:    m['영업이익률']   = round(op.get(yr, 0)    / rev_v * 100, 2)
            if net:   m['순이익률']     = round(net.get(yr, 0)   / rev_v * 100, 2)
            if cogs:  m['매출원가율']   = round(cogs.get(yr, 0)  / rev_v * 100, 2)
            if ebitda: m['EBITDA마진'] = round(ebitda.get(yr, 0) / rev_v * 100, 2)
        if sga and cogs and cogs.get(yr, 0):
            m['비용구조비율'] = round(sga.get(yr, 0) / cogs.get(yr, 0) * 100, 2)

        idx = years.index(yr)
        if idx > 0:
            prev = years[idx - 1]
            def _yoy(acc):
                p = acc.get(prev, 0)
                return round((acc.get(yr, 0) - p) / abs(p) * 100, 2) if p else None
            if rev:   m['매출액증가율']  = _yoy(rev)
            if gross: m['총이익증가율']  = _yoy(gross)
            if op:    m['영업이익증가율'] = _yoy(op)
            if net:   m['순이익증가율']  = _yoy(net)

        metrics[yr] = {k: v for k, v in m.items() if v is not None}
    return metrics


def calculate_common_metrics(bs_accounts, is_accounts, years):
    metrics = {}
    for yr in years:
        m = {}
        tot_ast = bs_accounts.get('자산총계') or {}
        eq      = bs_accounts.get('자본총계') or {}
        liab    = bs_accounts.get('부채총계') or {}
        rev     = is_accounts.get('매출액') or {}
        net     = is_accounts.get('당기순이익') or {}
        op      = is_accounts.get('영업이익') or {}
        cl      = bs_accounts.get('유동부채') or {}
        cash    = bs_accounts.get('현금및현금성자산') or {}
        cap     = bs_accounts.get('자본금') or {}
        # 스킬 Q4-1 이자보상배수 = 영업이익/이자비용. 이자비용 계정이 없을 때만 영업외비용으로 대체한다.
        opex    = is_accounts.get('이자비용') or is_accounts.get('영업외비용') or {}

        ast_v = tot_ast.get(yr, 0)
        eq_v  = eq.get(yr, 0)

        if net and tot_ast and ast_v: m['ROA']  = round(net.get(yr, 0) / ast_v * 100, 2)
        if net and eq      and eq_v:  m['ROE']  = round(net.get(yr, 0) / eq_v  * 100, 2)
        ic = ast_v - cl.get(yr, 0)
        if op and tot_ast and ic:     m['ROIC'] = round(op.get(yr, 0)  / ic    * 100, 2)
        if cap and net:
            shares = cap.get(yr, 0) / 1000
            if shares > 0: m['EPS'] = round(net.get(yr, 0) / shares, 0)
        if cash and liab and liab.get(yr, 0):
            m['부채대비현금비율'] = round(cash.get(yr, 0) / liab.get(yr, 0) * 100, 2)
        if op and opex and opex.get(yr, 0):
            m['이자보상배율'] = round(op.get(yr, 0) / abs(opex.get(yr, 0)), 2)
        if rev and eq      and eq_v:  m['자본회전율']       = round(rev.get(yr, 0) / eq_v  , 2)
        if op  and tot_ast and ast_v: m['자산대비영업이익률'] = round(op.get(yr, 0)  / ast_v * 100, 2)
        if op  and eq      and eq_v:  m['자본대비영업이익률'] = round(op.get(yr, 0)  / eq_v  * 100, 2)

        metrics[yr] = {k: v for k, v in m.items() if v is not None}
    return metrics


def compute_all_metrics(df_bs, df_is, years):
    """BS/IS에서 계정을 추출해 세 지표 딕셔너리(bs_metrics, is_metrics, common_metrics)를
    계산한다. 인터랙티브 화면(render_financial_metrics)과 고객용 자동분석 파이프라인
    (auto_pipeline.py) 양쪽에서 공유해, 계정 키워드 목록이 두 군데로 갈라지지 않게 한다."""
    bs_accounts = {
        '현금및현금성자산': find_account(df_bs, ['현금', '현금성자산', '예금', '당좌예금'], years),
        '단기금융자산':     find_account(df_bs, ['단기금융자산', '단기투자', '유동금융자산'], years),
        '매출채권':        find_account(df_bs, ['매출채권', '외상매출금', '거래외채권', '채권'], years),
        '재고자산':        find_account(df_bs, ['재고자산', '재고', '상품', '제품', '반제품', '원재료', '재공품'], years),
        '유동자산':        find_account(df_bs, ['유동자산'], years),
        '비유동자산':      find_account(df_bs, ['비유동자산', '고정자산', '투자자산'], years),
        '자산총계':        find_account(df_bs, ['자산총계', '총자산', '자산합계'], years),
        '유동부채':        find_account(df_bs, ['유동부채'], years),
        '부채총계':        find_account(df_bs, ['부채총계', '총부채', '부채합계'], years),
        '자본총계':        find_account(df_bs, ['자본총계', '자본합계', '순자산', '자본'], years),
        '자본금':          find_account(df_bs, ['자본금', '납입자본', '설립자본'], years),
        '매입채무':        find_account(df_bs, ['매입채무', '외상매입금'], years),
        '차입금':          sum_borrowings(df_bs, years),
    }
    is_accounts = {
        '매출액':    find_account(df_is, ['매출액', '매출', '수익', '총매출', '사업수익'], years),
        '매출원가':  find_account(df_is, ['매출원가', '원가', '판매원가', '제품원가'], years),
        '매출총이익': find_account(df_is, ['매출총이익', '매출총손익', 'gross', '총이익'], years),
        '판매관리비': find_account(df_is, ['판매관리비', '판매비', '관리비', '운영비'], years),
        '영업이익':  find_account(df_is, ['영업이익', '영업손익', '운영이익', '본이익'], years),
        'EBITDA':    find_account(df_is, ['EBITDA', '에비타'], years),
        '당기순이익': find_account(df_is, ['당기순이익', '당기순손익', '순이익', '당기순손실'], years),
        '영업외비용': find_account(df_is, ['영업외비용', '금융비용', '이자비용'], years),
        '이자비용':  find_account(df_is, ['이자비용'], years),
    }

    # 공사업은 매출채권 대신 공사미수금으로 매출 채권을 잡는다. 매출채권만 보면 회수기간이 0에
    # 가깝게 나와 현금전환주기가 음수로 왜곡되므로(예: 효성에너지팜 2023~2024) 함께 더한다.
    construction_ar = find_account(df_bs, ['공사미수금'], years)
    if construction_ar:
        base = bs_accounts['매출채권'] or {}
        bs_accounts['매출채권'] = {yr: base.get(yr, 0) + construction_ar.get(yr, 0) for yr in years}

    bs_metrics     = calculate_bs_metrics(bs_accounts, is_accounts, years)
    is_metrics     = calculate_is_metrics(is_accounts, years)
    common_metrics = calculate_common_metrics(bs_accounts, is_accounts, years)
    return bs_metrics, is_metrics, common_metrics


# ── 렌더링 ───────────────────────────────────────────────────────────────────

def render_financial_metrics(df_bs, df_is, years):
    st.markdown("---")
    st.markdown("### 3-1. 재무지표 연도별 추이")

    if not years:
        st.warning("연도 정보가 없습니다.")
        return

    bs_metrics, is_metrics, common_metrics = compute_all_metrics(df_bs, df_is, years)

    # ── 문서 포함 지표 선택 ──
    st.markdown("#### 문서 포함 지표 선택")

    col_reset, _ = st.columns([1, 4])
    with col_reset:
        if st.button("다시 선택하기", key="reset_indicators"):
            for prefix, inds in (('bs', BS_INDICATORS), ('is', IS_INDICATORS), ('common', COMMON_INDICATORS)):
                for ind in inds:
                    st.session_state[f"doc_{prefix}_{ind}"] = False
            st.rerun()

    st.markdown("**BS 지표**")
    selected_bs = _indicator_buttons("bs", BS_INDICATORS)

    st.markdown("**IS 지표**")
    selected_is = _indicator_buttons("is", IS_INDICATORS)

    st.markdown("**공통 지표**")
    selected_common = _indicator_buttons("common", COMMON_INDICATORS)

    st.session_state['selected_indicators'] = {'bs': selected_bs, 'is': selected_is, 'common': selected_common}

    # ── 지표 표 ──
    tab_bs, tab_is, tab_common = st.tabs(["재무상태표 (BS) 지표", "손익계산서 (IS) 지표", "공통 지표"])
    with tab_bs:
        st.dataframe(_metrics_df(bs_metrics, BS_INDICATORS, years), use_container_width=True)
    with tab_is:
        st.dataframe(_metrics_df(is_metrics, IS_INDICATORS, years), use_container_width=True)
    with tab_common:
        st.dataframe(_metrics_df(common_metrics, COMMON_INDICATORS, years), use_container_width=True)

    # ── 그래프 ──
    st.markdown("#### 재무지표 그래프")
    all_indicators = BS_INDICATORS + IS_INDICATORS + COMMON_INDICATORS
    graph_mode = st.radio("그래프 표시 방식", ["개별 지표 그래프", "지표 조합 그래프"], horizontal=True, key="graph_mode")

    if graph_mode == "개별 지표 그래프":
        sel = st.selectbox("표시할 지표 선택", all_indicators, key="graph_single")
        chart_data = [
            {'연도': str(yr), '값': v}
            for yr in years
            for v in [_get_metric_val(sel, yr, bs_metrics, is_metrics, common_metrics)]
            if v is not None
        ]
        if chart_data:
            fig = px.line(pd.DataFrame(chart_data), x='연도', y='값', markers=True, title=f"{sel} 연도별 추이")
            fig.update_traces(texttemplate='%{y}', textposition='top center')
            fig.update_layout(xaxis=dict(type='category'), yaxis=dict(showgrid=True), **_CHART_LAYOUT)
            st.plotly_chart(fig, use_container_width=True, config=_CHART_CONFIG)

    else:
        st.caption("보려는 목적에 맞는 추천 조합을 고르면 아래 선택창이 자동으로 채워집니다. 이후 직접 더하거나 빼도 됩니다.")
        combo_cols = st.columns(len(RECOMMENDED_COMBOS))
        for col, (combo_name, combo_indicators) in zip(combo_cols, RECOMMENDED_COMBOS.items()):
            with col:
                if st.button(combo_name, key=f"combo_{combo_name}", use_container_width=True):
                    st.session_state["chart_options"] = [i for i in combo_indicators if i in all_indicators]
                    st.rerun()

        chart_options = st.multiselect("표시할 지표 선택 (복수)", all_indicators, default=all_indicators[:4], key="chart_options")
        chart_type    = st.radio("그래프 유형", ["선 그래프", "묶음 막대 그래프"], horizontal=True, key="chart_type")

        if chart_options:
            chart_data = [
                {'지표': ind, '연도': str(yr), '값': v}
                for ind in chart_options
                for yr in years
                for v in [_get_metric_val(ind, yr, bs_metrics, is_metrics, common_metrics)]
                if v is not None
            ]
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                if chart_type == "선 그래프":
                    fig = px.line(df_chart, x='연도', y='값', color='지표', markers=True,
                                  color_discrete_sequence=_CATEGORICAL_COLORS)
                    fig.update_traces(texttemplate='%{y}', textposition='top center')
                else:
                    fig = px.bar(df_chart, x='연도', y='값', color='지표', barmode='group',
                                 color_discrete_sequence=_CATEGORICAL_COLORS)
                    fig.update_traces(texttemplate='%{y}', textposition='outside')
                fig.update_layout(
                    title="재무지표 연도별 추이",
                    xaxis=dict(type='category'), yaxis=dict(showgrid=True),
                    legend_title="지표",
                    **_CHART_LAYOUT,
                )
                st.plotly_chart(fig, use_container_width=True, config=_CHART_CONFIG)

    return bs_metrics, is_metrics, common_metrics, years


def _pick_won_scale(values):
    """금액 시리즈(원 단위)를 억/백만원 중 어느 단위로 보여줄지 고른다. 시리즈 최댓값이
    1억 미만인 작은 회사에서 '억' 단위를 그대로 쓰면 소수점 1자리로도 0.0이 나와버려서,
    그럴 때만 백만원 단위로 전환해 자릿수를 확보한다. 반환: (나눌 값, 단위 라벨)."""
    nums = [abs(v) for v in values if v is not None]
    if nums and max(nums) < 1e8:
        return 1e6, "백만원"
    return 1e8, "억"


def _find_account_values(df, keyword, years):
    """df(원본 계정 x 연도)에서 계정과목에 keyword가 포함된 첫 행을 찾아 연도별 원본 금액을
    반환한다. 회사마다 "부채총계", "부채총계(Ⅰ+Ⅱ)" 등 표기가 달라 정확히 일치시키기 어려워
    부분 일치로 찾는다. 못 찾으면 None을 반환해(값 전체가 아닌 개별 반환), 호출부가 그
    계정이 빠진 콤보 차트를 만들지 말지 판단할 수 있게 한다."""
    if df is None:
        return None
    match = df[df["계정과목"].astype(str).str.contains(keyword, na=False)]
    if match.empty:
        return None
    row = match.iloc[0]
    try:
        return [float(row.get(y, 0) or 0) for y in years]
    except (TypeError, ValueError):
        return None


# 보고서용 차트 PNG — report.py가 약 11cm 폭으로 넣는다. 그 크기에서 글자가 8~9pt로 읽히도록
# 픽셀 글꼴 크기를 정한다(800px 폭 → 1px ≈ 0.14mm, 22px ≈ 3mm ≈ 8.7pt).
_CHART_PNG_SIZE = dict(width=800, height=520, scale=2)
_CHART_PNG_FONT = 22
_CHART_PNG_TITLE_FONT = 26


def _png_layout(title):
    return dict(
        title=dict(text=title, font=dict(size=_CHART_PNG_TITLE_FONT)),
        font=dict(color='#191919', size=_CHART_PNG_FONT, family='Malgun Gothic, Arial'),
        template='plotly_white', paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text=''),
        margin=dict(l=70, r=70, t=110, b=50),
        xaxis=dict(type='category', showgrid=False),
    )


def _value_labels(values, fmt):
    """3개년 이내 추이라 모든 점이 시작·변곡·종료점이다 — 점마다 값을 붙인다(값 없는 해는 비움)."""
    return [fmt.format(v) if v is not None else '' for v in values]


def _build_combo_chart_png(title, bar_series, line_series, years, bar_unit, line_unit='%'):
    """막대(1~2개, 왼쪽 축) + 선(1개, 오른쪽 축)으로 된 콤보 차트를 PNG 바이트로 만든다.
    bar_series/line_series: [(이름, 값리스트), ...] — 범례 이름은 호출부가 옆에 두는 원본
    데이터 표의 행 이름과 정확히 같은 문자열을 넘겨야 한다(차트 제목·범례는 원천 표와
    동일해야 한다는 Q4-4 규칙). 축 제목에 단위를 적는다(Q4-4 차트 작성 공통 가이드)."""
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for i, (name, values) in enumerate(bar_series):
        fig.add_trace(
            go.Bar(x=years, y=values, name=name, marker_color=_CATEGORICAL_COLORS[i % len(_CATEGORICAL_COLORS)],
                   text=_value_labels(values, '{:.1f}'), textposition='outside', cliponaxis=False),
            secondary_y=False,
        )
    for i, (name, values) in enumerate(line_series):
        color = _CATEGORICAL_COLORS[(len(bar_series) + i) % len(_CATEGORICAL_COLORS)]
        fig.add_trace(
            go.Scatter(x=years, y=values, name=name, mode="lines+markers+text", line=dict(color=color, width=3),
                       marker=dict(size=10), text=_value_labels(values, '{:.1f}' + line_unit),
                       textposition='top center', cliponaxis=False),
            secondary_y=True,
        )

    fig.update_layout(barmode="group", **_png_layout(title))
    fig.update_yaxes(title_text=f"(단위: {bar_unit})", showgrid=True, gridcolor="#E5E5E5", rangemode='tozero',
                     secondary_y=False)
    fig.update_yaxes(title_text=f"(단위: {line_unit})", showgrid=False, rangemode='tozero', secondary_y=True)
    return fig.to_image(format="png", **_CHART_PNG_SIZE)


def _build_line_chart_png(title, series, years, secondary=(), unit='%'):
    """고정 색상 팔레트를 쓰는 N선 꺾은선 차트 — '수익성 지표' 같은 여러 지표 비교용.
    secondary에 든 이름의 선은 오른쪽 축에 그린다. 매출원가율(80~100%)처럼 다른 선과 크기
    차이가 큰 지표를 같은 축에 두면 나머지 선(판관비율·영업이익률 5~10%)이 바닥에 깔려
    변화가 보이지 않기 때문이다. 축 제목에 어느 선이 어느 축인지 적는다."""
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    fig = make_subplots(specs=[[{"secondary_y": bool(secondary)}]])
    left_names, right_names = [], []
    for i, (name, values) in enumerate(series):
        color = _CATEGORICAL_COLORS[i % len(_CATEGORICAL_COLORS)]
        on_right = name in secondary
        (right_names if on_right else left_names).append(name)
        trace = go.Scatter(x=years, y=values, name=name, mode="lines+markers+text",
                           line=dict(color=color, width=3, dash='dot' if on_right else 'solid'),
                           marker=dict(size=10), text=_value_labels(values, '{:.1f}' + unit),
                           textposition='top center', cliponaxis=False)
        if secondary:
            fig.add_trace(trace, secondary_y=on_right)
        else:
            fig.add_trace(trace)

    fig.update_layout(**_png_layout(title))
    left_title = f"{'·'.join(left_names)} (단위: {unit})" if secondary else f"(단위: {unit})"
    fig.update_yaxes(title_text=left_title, showgrid=True, gridcolor="#E5E5E5", secondary_y=False if secondary else None)
    if secondary:
        fig.update_yaxes(title_text=f"{'·'.join(right_names)} (단위: {unit})", showgrid=False, secondary_y=True)
    return fig.to_image(format="png", **_CHART_PNG_SIZE)
