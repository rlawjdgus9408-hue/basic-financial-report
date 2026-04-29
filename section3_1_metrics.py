"""
Section 3-1: 재무지표 연도별 추이
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def find_account(df, keywords, years):
    """계정 검색 - 연도별 값 딕셔너리로 반환 (여러 키워드 지원)"""
    for kw in keywords:
        matches = df[df['계정과목'].str.contains(kw, case=False, na=False)]
        if not matches.empty:
            row = matches.iloc[0]
            result = {}
            for yr in years:
                if yr in row.index:
                    val = row[yr]
                    try:
                        result[yr] = float(val) if pd.notna(val) else 0
                    except:
                        result[yr] = 0
            return result
    return None

def calculate_bs_metrics(bs_accounts, is_accounts, years):
    """BS 기반 지표 계산"""
    metrics = {}
    for yr in years:
        metrics[yr] = {}
        
        ca = bs_accounts.get('유동자산')
        cl = bs_accounts.get('유동부채')
        inv = bs_accounts.get('재고자산', {})
        cash = bs_accounts.get('현금및현금성자산', {})
        liabilities = bs_accounts.get('부채총계', {})
        equity = bs_accounts.get('자본총계', {})
        assets = bs_accounts.get('자산총계', {})
        nca = bs_accounts.get('비유동자산', {})
        ar = bs_accounts.get('매출채권', {})
        revenue = is_accounts.get('매출액', {})
        cogs = is_accounts.get('매출원가', {})
        
        # 유동비율
        if ca and cl and cl.get(yr, 0) != 0:
            metrics[yr]['유동비율'] = round(ca.get(yr, 0) / cl.get(yr, 0) * 100, 2)
        
        # 당좌비율
        if ca and cl and cl.get(yr, 0) != 0:
            quick_assets = ca.get(yr, 0) - inv.get(yr, 0)
            metrics[yr]['당좌비율'] = round(quick_assets / cl.get(yr, 0) * 100, 2)
        
        # 현금비율
        if cash and cl and cl.get(yr, 0) != 0:
            metrics[yr]['현금비율'] = round(cash.get(yr, 0) / cl.get(yr, 0) * 100, 2)
        
        # 부채비율
        if equity and equity.get(yr, 0) != 0:
            metrics[yr]['부채비율'] = round(liabilities.get(yr, 0) / equity.get(yr, 0) * 100, 2)
        
        # 자기자본비율
        if assets and equity and equity.get(yr, 0) != 0:
            metrics[yr]['자기자본비율'] = round(equity.get(yr, 0) / assets.get(yr, 0) * 100, 2)
        
        # 유동부채비율
        if ca and cl and ca.get(yr, 0) != 0:
            metrics[yr]['유동부채비율'] = round(cl.get(yr, 0) / ca.get(yr, 0) * 100, 2)
        
        # 비유동자산비율
        if nca and assets and assets.get(yr, 0) != 0:
            metrics[yr]['비유동자산비율'] = round(nca.get(yr, 0) / assets.get(yr, 0) * 100, 2)
        
        # 재고자산비율
        if inv and ca and ca.get(yr, 0) != 0:
            metrics[yr]['재고자산비율'] = round(inv.get(yr, 0) / ca.get(yr, 0) * 100, 2)
        
        # 매출채권회전율
        if ar and revenue and ar.get(yr, 0) != 0:
            metrics[yr]['매출채권회전율'] = round(revenue.get(yr, 0) / ar.get(yr, 0), 2)
        
        # 재고자산회전율
        if inv and cogs and inv.get(yr, 0) != 0:
            metrics[yr]['재고자산회전율'] = round(cogs.get(yr, 0) / inv.get(yr, 0), 2)
        
        # 총자산회전율
        if revenue and assets and assets.get(yr, 0) != 0:
            metrics[yr]['총자산회전율'] = round(revenue.get(yr, 0) / assets.get(yr, 0), 2)
    
    return metrics

def calculate_is_metrics(is_accounts, years):
    """IS 기반 지표 계산"""
    metrics = {}
    for yr in years:
        metrics[yr] = {}
        revenue = is_accounts.get('매출액', {})
        cogs = is_accounts.get('매출원가', {})
        gross = is_accounts.get('매출총이익', {})
        op = is_accounts.get('영업이익', {})
        net = is_accounts.get('당기순이익', {})
        sga = is_accounts.get('판매관리비', {})
        
        # 매출총이익률
        if gross and revenue and revenue.get(yr, 0) != 0:
            metrics[yr]['매출총이익률'] = round(gross.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
        
        # 판매관리비율
        if sga and revenue and revenue.get(yr, 0) != 0:
            metrics[yr]['판매관리비율'] = round(sga.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
        
        # 영업이익률
        if op and revenue and revenue.get(yr, 0) != 0:
            metrics[yr]['영업이익률'] = round(op.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
        
        # 순이익률
        if net and revenue and revenue.get(yr, 0) != 0:
            metrics[yr]['순이익률'] = round(net.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
        
        # 매출원가율
        if cogs and revenue and revenue.get(yr, 0) != 0:
            metrics[yr]['매출원가율'] = round(cogs.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
        
        # EBITDA마진
        if op and revenue and revenue.get(yr, 0) != 0:
            metrics[yr]['EBITDA마진'] = round(op.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
        
        # 비용구조비율
        if sga and cogs and cogs.get(yr, 0) != 0:
            metrics[yr]['비용구조비율'] = round(sga.get(yr, 0) / cogs.get(yr, 0) * 100, 2)
        
        # YoY 성장률
        idx = years.index(yr)
        if idx > 0 and revenue:
            prev_yr = years[idx - 1]
            if revenue.get(prev_yr, 0) != 0:
                metrics[yr]['매출액증가율'] = round((revenue.get(yr, 0) - revenue.get(prev_yr, 0)) / revenue.get(prev_yr, 0) * 100, 2)
        
        if idx > 0 and gross:
            prev_yr = years[idx - 1]
            if gross.get(prev_yr, 0) != 0:
                metrics[yr]['총이익증가율'] = round((gross.get(yr, 0) - gross.get(prev_yr, 0)) / gross.get(prev_yr, 0) * 100, 2)
        
        if idx > 0 and op:
            prev_yr = years[idx - 1]
            if op.get(prev_yr, 0) != 0:
                metrics[yr]['영업이익증가율'] = round((op.get(yr, 0) - op.get(prev_yr, 0)) / abs(op.get(prev_yr, 0)) * 100, 2)
        
        if idx > 0 and net:
            prev_yr = years[idx - 1]
            if net.get(prev_yr, 0) != 0:
                metrics[yr]['순이익증가율'] = round((net.get(yr, 0) - net.get(prev_yr, 0)) / abs(net.get(prev_yr, 0)) * 100, 2)
    
    return metrics

def calculate_common_metrics(bs_accounts, is_accounts, years):
    """BS + IS 공통 지표 계산"""
    metrics = {}
    for yr in years:
        metrics[yr] = {}
        
        assets = bs_accounts.get('자산총계', {})
        equity = bs_accounts.get('자본총계', {})
        liabilities = bs_accounts.get('부채총계', {})
        revenue = is_accounts.get('매출액', {})
        net = is_accounts.get('당기순이익', {})
        op = is_accounts.get('영업이익', {})
        cl = bs_accounts.get('유동부채', {})
        cash = bs_accounts.get('현금및현금성자산', {})
        capital = bs_accounts.get('자본금', {})
        opex = is_accounts.get('영업외비용', {})
        
        # ROA
        if net and assets and assets.get(yr, 0) != 0:
            metrics[yr]['ROA'] = round(net.get(yr, 0) / assets.get(yr, 0) * 100, 2)
        
        # ROE
        if net and equity and equity.get(yr, 0) != 0:
            metrics[yr]['ROE'] = round(net.get(yr, 0) / equity.get(yr, 0) * 100, 2)
        
        # ROIC
        if op and assets and (assets.get(yr, 0) - cl.get(yr, 0)) != 0:
            ic = assets.get(yr, 0) - cl.get(yr, 0)
            metrics[yr]['ROIC'] = round(op.get(yr, 0) / ic * 100, 2)
        
        # EPS
        if capital and net and capital.get(yr, 0) and capital.get(yr, 0) > 0:
            shares = capital.get(yr, 0) / 1000
            if shares > 0:
                metrics[yr]['EPS'] = round(net.get(yr, 0) / shares, 0)
        
        # 부채대비현금비율
        if cash and liabilities and liabilities.get(yr, 0) != 0:
            metrics[yr]['부채대비현금비율'] = round(cash.get(yr, 0) / liabilities.get(yr, 0) * 100, 2)
        
        # 이자보상배율
        if op and opex and opex.get(yr, 0):
            metrics[yr]['이자보상배율'] = round(op.get(yr, 0) / abs(opex.get(yr, 0)), 2)
        
        # 자본회전율
        if revenue and equity and equity.get(yr, 0) != 0:
            metrics[yr]['자본회전율'] = round(revenue.get(yr, 0) / equity.get(yr, 0), 2)
        
        # 자산대비영업이익률
        if op and assets and assets.get(yr, 0) != 0:
            metrics[yr]['자산대비영업이익률'] = round(op.get(yr, 0) / assets.get(yr, 0) * 100, 2)
        
        # 자본대비영업이익률
        if op and equity and equity.get(yr, 0) != 0:
            metrics[yr]['자본대비영업이익률'] = round(op.get(yr, 0) / equity.get(yr, 0) * 100, 2)
    
    return metrics

def render_financial_metrics(df_bs, df_is, years):
    """재무지표 연도별 추이 렌더링"""
    st.markdown("---")
    st.markdown("### 3-1. 재무지표 연도별 추이")
    
    if not years:
        st.warning("연도 정보가 없습니다.")
        return
    
    # BS 계정 추출 (더 많은 키워드)
    bs_accounts = {
        '현금및현금성자산': find_account(df_bs, ['현금', '현금성자산', '예금', '당좌예금', '현금및'], years),
        '단기금융자산': find_account(df_bs, ['단기금융자산', '단기투자', '유동금융자산'], years),
        '매출채권': find_account(df_bs, ['매출채권', '채권', '외상매출금', '거래외채권', '채권'], years),
        '재고자산': find_account(df_bs, ['재고', '재고자산', '상품', '제품', '반제품', '원재료', '재공품', '재고'], years),
        '유동자산': find_account(df_bs, ['유동자산', '流动자산'], years),
        '비유동자산': find_account(df_bs, ['비유동자산', '고정자산', '투자자산'], years),
        '자산총계': find_account(df_bs, ['자산총계', '총자산', '자산합계', '자산'], years),
        '유동부채': find_account(df_bs, ['유동부채', '流动부채'], years),
        '부채총계': find_account(df_bs, ['부채총계', '총부채', '부채합계', '부채'], years),
        '자본총계': find_account(df_bs, ['자본총계', '자본합계', '순자산', '자본'], years),
        '자본금': find_account(df_bs, ['자본금', '납입자본', '설립자본'], years),
    }
    
    # IS 계정 추출 (더 많은 키워드)
    is_accounts = {
        '매출액': find_account(df_is, ['매출액', '매출', '수익', '총매출', '사업수익', '매출'], years),
        '매출원가': find_account(df_is, ['매출원가', '원가', '판매원가', '제품원가', '원가'], years),
        '매출총이익': find_account(df_is, ['매출총이익', 'gross', '총이익', '매출총이익'], years),
        '판매관리비': find_account(df_is, ['판매관리비', '판매비', '관리비', '운영비', '판매비'], years),
        '영업이익': find_account(df_is, ['영업이익', '운영이익', '본이익', '영업이익'], years),
        '당기순이익': find_account(df_is, ['당기순이익', '순이익', '당기순손실', '순이익'], years),
        '영업외비용': find_account(df_is, ['영업외비용', '금융비용', '이자비용'], years),
    }
    
    # 지표 계산
    bs_metrics = calculate_bs_metrics(bs_accounts, is_accounts, years)
    is_metrics = calculate_is_metrics(is_accounts, years)
    common_metrics = calculate_common_metrics(bs_accounts, is_accounts, years)
    
    # 지표 목록 정의
    bs_indicators = ['유동비율', '당좌비율', '현금비율', '부채비율', '자기자본비율', '유동부채비율', '비유동자산비율', '재고자산비율', '매출채권회전율', '재고자산회전율', '총자산회전율']
    is_indicators = ['매출총이익률', '판매관리비율', '영업이익률', '순이익률', '매출원가율', 'EBITDA마진', '비용구조비율', '매출액증가율', '총이익증가율', '영업이익증가율', '순이익증가율']
    common_indicators = ['ROA', 'ROE', 'ROIC', 'EPS', '부채대비현금비율', '이자보상배율', '자본회전율', '자산대비영업이익률', '자본대비영업이익률']
    
    # ============ 문서 포함용 지표 선택 ============
    st.markdown("#### 📄 문서 포함 지표 선택")
    col_doc1, col_doc2 = st.columns(2)
    
    with col_doc1:
        st.markdown("**BS 지표**")
        selected_bs = []
        for ind in bs_indicators:
            if st.checkbox(f"  {ind}", value=True, key=f"doc_bs_{ind}"):
                selected_bs.append(ind)
    
    with col_doc2:
        st.markdown("**IS 지표**")
        selected_is = []
        for ind in is_indicators:
            if st.checkbox(f"  {ind}", value=True, key=f"doc_is_{ind}"):
                selected_is.append(ind)
    
    st.markdown("**공통 지표**")
    selected_common = []
    for ind in common_indicators:
        if st.checkbox(f"  {ind}", value=True, key=f"doc_common_{ind}"):
            selected_common.append(ind)
    
    # 선택된 지표를 세션에 저장
    st.session_state['selected_indicators'] = {
        'bs': selected_bs,
        'is': selected_is,
        'common': selected_common
    }
    
    # ============ 탭으로 구분하여 표시 ============
    tab_bs_metrics, tab_is_metrics, tab_common = st.tabs(["📊 재무상태표 (BS) 지표", "📈 손익계산서 (IS) 지표", "🔗 공통 지표"])
    
    # BS 지표
    with tab_bs_metrics:
        bs_df = pd.DataFrame(index=bs_indicators, columns=years)
        for yr in years:
            for ind in bs_indicators:
                if bs_metrics[yr].get(ind) is not None:
                    bs_df.loc[ind, yr] = bs_metrics[yr][ind]
        st.dataframe(bs_df.astype(str).replace('nan', '-').replace('None', '-'), use_container_width=True)
    
    # IS 지표
    with tab_is_metrics:
        is_df = pd.DataFrame(index=is_indicators, columns=years)
        for yr in years:
            for ind in is_indicators:
                if is_metrics[yr].get(ind) is not None:
                    is_df.loc[ind, yr] = is_metrics[yr][ind]
        st.dataframe(is_df.astype(str).replace('nan', '-').replace('None', '-'), use_container_width=True)
    
    # 공통 지표
    with tab_common:
        common_df = pd.DataFrame(index=common_indicators, columns=years)
        for yr in years:
            for ind in common_indicators:
                if common_metrics[yr].get(ind) is not None:
                    common_df.loc[ind, yr] = common_metrics[yr][ind]
        st.dataframe(common_df.astype(str).replace('nan', '-').replace('None', '-'), use_container_width=True)
    
    # ============ 그래프 시각화 ============
    st.markdown("#### 📈 재무지표 그래프")
    
    # 그래프 표시 방식 선택
    graph_mode = st.radio("그래프 표시 방식", ["개별 지표 그래프", "지표 조합 그래프"], horizontal=True, key="graph_mode")
    
    all_indicators = bs_indicators + is_indicators + common_indicators
    
    if graph_mode == "개별 지표 그래프":
        # 개별 지표 선택
        selected_graph = st.selectbox("표시할 지표 선택", all_indicators, key="graph_single")
        
        chart_data = []
        for yr in years:
            val = None
            if selected_graph in bs_metrics[yr]:
                val = bs_metrics[yr][selected_graph]
            elif selected_graph in is_metrics[yr]:
                val = is_metrics[yr][selected_graph]
            elif selected_graph in common_metrics[yr]:
                val = common_metrics[yr][selected_graph]
            
            if val is not None:
                chart_data.append({'연도': yr, '값': val})
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            # 연도를 문자열로 변환하여 범주형으로 처리
            df_chart['연도'] = df_chart['연도'].astype(str)
            fig = px.line(df_chart, x='연도', y='값', markers=True, title=f"{selected_graph} 연도별 추이")
            # 데이터 라벨링 추가
            fig.update_traces(texttemplate='%{y}', textposition='top center')
            fig.update_layout(
                xaxis_title="연도", 
                yaxis_title="값",
                xaxis=dict(type='category'),  # 연도를 범주형으로
                yaxis=dict(showgrid=True)  # 자동 눈금
            )
            # 복사/저장 기능
            st.plotly_chart(fig, use_container_width=True, config={
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': f'{selected_graph}_graph',
                    'height': 500,
                    'width': 800,
                    'scale': 2
                },
                'displayModeBar': True,
                'displaylogo': False
            })
    
    else:
        # 조합 그래프 (여러 지표 동시 표시)
        chart_options = st.multiselect("📊 표시할 지표 선택 (복수 선택 가능)", all_indicators, default=all_indicators[:4], key="chart_options")
        
        # 그래프 유형 선택
        chart_type = st.radio("그래프 유형", ["선 그래프", "묶음 막대 그래프"], horizontal=True, key="chart_type")
        
        if chart_options:
            chart_data = []
            for ind in chart_options:
                for yr in years:
                    val = None
                    if ind in bs_metrics[yr]:
                        val = bs_metrics[yr][ind]
                    elif ind in is_metrics[yr]:
                        val = is_metrics[yr][ind]
                    elif ind in common_metrics[yr]:
                        val = common_metrics[yr][ind]
                    
                    if val is not None:
                        chart_data.append({'지표': ind, '연도': yr, '값': val})
            
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                # 연도를 문자열로 변환하여 범주형으로 처리
                df_chart['연도'] = df_chart['연도'].astype(str)
                
                if chart_type == "선 그래프":
                    fig = px.line(df_chart, x='연도', y='값', color='지표', markers=True)
                    fig.update_traces(texttemplate='%{y}', textposition='top center')
                else:
                    fig = px.bar(df_chart, x='연도', y='값', color='지표', barmode='group')
                    fig.update_traces(texttemplate='%{y}', textposition='outside')
                
                fig.update_layout(
                    title="재무지표 연도별 추이 (복수 지표)", 
                    xaxis_title="연도", 
                    yaxis_title="값", 
                    legend_title="지표",
                    xaxis=dict(type='category'),  # 연도를 범주형으로
                    yaxis=dict(showgrid=True)  # 자동 눈금
                )
                st.plotly_chart(fig, use_container_width=True, config={
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': 'financial_indicators_graph',
                        'height': 500,
                        'width': 800,
                        'scale': 2
                    },
                    'displayModeBar': True,
                    'displaylogo': False
                })
    
    return bs_metrics, is_metrics, common_metrics, years