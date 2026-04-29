import streamlit as st
import pandas as pd
import io
from docxtpl import DocxTemplate
import datetime
import traceback
import re
import time  # 퍼센트 게이지를 위한 모듈 추가

st.set_page_config(page_title="그로스파이낸스 재무진단 시스템", layout="wide")
st.title("🛡️ 그로스파이낸스 기초재무진단 자동화 시스템")

# 세션 상태 초기화 함수
def init_session_state():
    defaults = {
        'company_name': '',
        'biz_type': '',
        'ceo_name': '',
        'biz_start_date': '',
        'biz_no': '',
        'phone': '',
        'email': '',
        'address': '',
        'emp_count': '',
        'erp_system': '',
        'exec_summary': '',
        'finance_comment': '',
        'account_comment': '',
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# 1. 기업 상세 정보 입력 (placeholder 추가)
st.markdown("### 1. 기업 상세 정보 입력")
col_info1, col_info2 = st.columns(2)

# 업종코드 CSV 파일 로드
@st.cache_data
def load_ksic_data():
    try:
        df = pd.read_csv("업종코드_참조.csv", encoding="utf-8")
        # 업태별 그룹화
        categories = df.groupby("업태")["업종코드"].apply(list).to_dict()
        return categories
    except:
        return {
            "농업": ["곡물 재배", "축산", "농업 서비스", "임업", "어업"],
            "제조업": ["Food 제조", "전자부품 제조", "자동차 제조"],
            "서비스": ["전문 서비스", "교육 서비스", "의료 서비스"]
        }

ksic_categories = load_ksic_data()

# 대분류 변경 시 소분류 초기화
if 'prev_biz_major' not in st.session_state:
    st.session_state.prev_biz_major = list(ksic_categories.keys())[0]

# 유효한 키만 사용
valid_keys = list(ksic_categories.keys())
current_biz_major = st.session_state.get('input_biz_major')
if current_biz_major not in valid_keys:
    current_biz_major = valid_keys[0]

if current_biz_major != st.session_state.prev_biz_major:
    st.session_state.prev_biz_major = current_biz_major
    st.session_state.input_biz_minor = ksic_categories[current_biz_major][0]

with col_info1:
    company_name = st.text_input("🏢 진단 기업명", value=st.session_state.company_name, placeholder="예:Growth파이낸스", key="input_co_name")
    
    # 업종: 업태/업종코드 선택
    col_biz1, col_biz2 = st.columns(2)
    with col_biz1:
        biz_major = st.selectbox("🏭 업태", valid_keys, index=valid_keys.index(current_biz_major), key="input_biz_major")
    with col_biz2:
        biz_minor = st.selectbox("🏭 업종코드", ksic_categories[biz_major], key="input_biz_minor")
    biz_type = f"{biz_major} > {biz_minor}"
    
    ceo_name = st.text_input("👤 대표자명", value=st.session_state.ceo_name, placeholder="예:홍길동", key="input_ceo_name")
    biz_start_date = st.text_input("📅 사업개시일", value=st.session_state.biz_start_date, placeholder="예:2024-01-01", key="input_biz_start")
    biz_no = st.text_input("🔢 사업자번호", value=st.session_state.biz_no, placeholder="예:000-00-00000", key="input_biz_no")

with col_info2:
    phone = st.text_input("📞 연락처", value=st.session_state.phone, placeholder="예:000-0000-0000(-없이 입력해주세요)", key="input_phone")
    
    # 이메일: 한 줄로 표시 (아이디 @ 도메인)
    col_email1, col_email2 = st.columns([3, 2])
    with col_email1:
        email_local = st.text_input("📧 이메일", value=st.session_state.email.split('@')[0] if '@' in st.session_state.email else st.session_state.email, placeholder="example", key="input_email_local")
    with col_email2:
        email_domain = st.selectbox("도메인", 
            ["gmail.com", "naver.com", "kakao.com", "hanmail.net", "nate.com", "hotmail.com", "icloud.com", "직접 입력"], 
            index=7, key="input_email_domain")
    if email_domain == "직접 입력":
        email_domain = st.text_input("직접 입력할 도메인", placeholder="example.com", key="input_email_custom")
    full_email = f"{email_local}@{email_domain}" if email_local and email_domain else ""
    
    address = st.text_input("📍 주소", value=st.session_state.address, placeholder="예:서울시 금천구 가산디지털1로", key="input_address")
    emp_count = st.text_input("👥 임직원 수 (숫자만)", value=st.session_state.emp_count, placeholder="예:10", key="input_emp_count")
    
    # 활용시스템: 선택창으로 변경
    erp_options = ["이카운트", "더존위고", "더존비즈", "ERP", "ACS", "원스", "고려시스템", "기타"]
    erp_system = st.selectbox("🖥️ 활용 시스템", erp_options, index=erp_options.index(st.session_state.erp_system) if st.session_state.erp_system in erp_options else 0, key="input_erp")

st.markdown("---")
st.markdown("### 2. 자료 업로드")
col_up1, col_up2 = st.columns(2)
uploaded_file = col_up1.file_uploader("재무진단 엑셀(RAW) 업로드", type=["xlsx"])
template_file = col_up2.file_uploader("워드 템플릿(.docx) 업로드", type=["docx"])

if uploaded_file:
    try:  # <--- 파이썬이 이 'try'의 짝꿍인 'except'를 맨 밑에서 찾지 못해서 났던 에러입니다!
        # --- [재무 데이터 파싱 로직] ---
        df_raw_full = pd.read_excel(uploaded_file, sheet_name='RAW', engine='openpyxl', header=None)
        
        header_idx = -1
        year_cols_dict = {}
        for idx, row in df_raw_full.iterrows():
            found = {c: m.group(1) for c, v in enumerate(row) if (m := re.search(r'(20\d{2})', str(v)))}
            if len(found) >= 2:
                header_idx, year_cols_dict = idx, found
                break

        if header_idx != -1:
            def get_clean_data(source_df, start, end=None):
                subset = source_df.iloc[start:end].copy()
                name_data = subset.iloc[:, 0:3].fillna("").astype(str)
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

            st.markdown("### 3. 재무 데이터 검토")
            tab_bs, tab_is = st.tabs(["🏛️ 재무상태표 (BS)", "📈 손익계산서 (IS)"])
            tab_bs.data_editor(df_bs, use_container_width=True, key="bs_editor")
            tab_is.data_editor(df_is, use_container_width=True, key="is_editor")

            # 3-1. 재무지표 연도별 추이
            st.markdown("---")
            st.markdown("### 3-1. 재무지표 연도별 추이")
            
            # 연도 목록
            years = list(year_cols_dict.values())
            
            # BS/IS 계정 찾기 (여러 키워드 지원) - 연도별 값 딕셔너리로 반환
            def find_account(df, keywords):
                for kw in keywords:
                    matches = df[df['계정과목'].str.contains(kw, case=False, na=False)]
                    if not matches.empty:
                        row = matches.iloc[0]
                        # 계정과목 제외하고 연도별 값만 추출
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
            
            # ============ BS 계정 추출 ============
            bs_accounts = {
                '현금및현금성자산': find_account(df_bs, ['현금', '현금성자산', '현금및현금성자산', '예금', '당좌예금']),
                '단기금융자산': find_account(df_bs, ['단기금융자산', '단기투자', '유동금융자산']),
                '매출채권': find_account(df_bs, ['매출채권', '채권', '외상매출금', '거래외채권']),
                '기타채권': find_account(df_bs, ['기타채권', '대여금']),
                '재고자산': find_account(df_bs, ['재고', '재고자산', '상품', '제품', '반제품', '원재료', '재공품']),
                '유동자산': find_account(df_bs, ['유동자산']),
                '비유동자산': find_account(df_bs, ['비유동자산', '고정자산']),
                '투자부동산': find_account(df_bs, ['투자부동산', '투자용 부동산']),
                '유형자산': find_account(df_bs, ['유형자산', '설비']),
                '무형자산': find_account(df_bs, ['무형자산', '특허권', '상호권']),
                '기타비유동자산': find_account(df_bs, ['기타비유동자산', '장기투자']),
                '자산총계': find_account(df_bs, ['자산총계', '총자산', '자산합계']),
                '매입채무': find_account(df_bs, ['매입채무', '외상매입금', '채무']),
                '단기차입금': find_account(df_bs, ['단기차입금', '단기차입']),
                '미지급금': find_account(df_bs, ['미지급금', '지급금']),
                '미지급비용': find_account(df_bs, ['미지급비용']),
                '예수금': find_account(df_bs, ['예수금', '보증금']),
                '유동부채': find_account(df_bs, ['유동부채']),
                '장기차입금': find_account(df_bs, ['장기차입금', '장기차입']),
                '비유동부채': find_account(df_bs, ['비유동부채', '고정부채']),
                '부채총계': find_account(df_bs, ['부채총계', '총부채', '부채합계']),
                '자본금': find_account(df_bs, ['자본금', '납입자본', '설립자본']),
                '자본잉여금': find_account(df_bs, ['자본잉여금']),
                '이익잉여금': find_account(df_bs, ['이익잉여금', '이익준비금']),
                '자본총계': find_account(df_bs, ['자본총계', '자본합계', '순자산']),
            }
            
            # ============ IS 계정 추출 ============
            is_accounts = {
                '매출액': find_account(df_is, ['매출액', '매출', '수익', '총매출', '사업수익']),
                '매출원가': find_account(df_is, ['매출원가', '원가', '판매원가', '제품원가']),
                '매출총이익': find_account(df_is, ['매출총이익', 'gross', '총이익']),
                '판매관리비': find_account(df_is, ['판매관리비', '판매비', '관리비', '운영비']),
                '영업이익': find_account(df_is, ['영업이익', '운영이익', '본이익']),
                '영업외수익': find_account(df_is, ['영업외수익', '기타수익', '금융수익']),
                '영업외비용': find_account(df_is, ['영업외비용', '기타비용', '금융비용']),
                '법인세비용': find_account(df_is, ['법인세', '세금']),
                '당기순이익': find_account(df_is, ['당기순이익', '순이익', '당기순손실']),
                '감가상각비': find_account(df_is, ['감가상각', '상각']),
            }
            
            # ============ 지표 계산 함수 ============
            def calculate_bs_metrics(bs_accounts, years):
                """BS 기반 지표"""
                metrics = {}
                for yr in years:
                    metrics[yr] = {}
                    
                    # 유동비율
                    ca = bs_accounts.get('유동자산')
                    cl = bs_accounts.get('유동부채')
                    if ca and cl and cl.get(yr, 0) != 0:
                        metrics[yr]['유동비율'] = round(ca.get(yr, 0) / cl.get(yr, 0) * 100, 2)
                    
                    # 당좌비율
                    inv = bs_accounts.get('재고자산', {})
                    if ca and cl and cl.get(yr, 0) != 0:
                        quick_assets = ca.get(yr, 0) - inv.get(yr, 0)
                        metrics[yr]['당좌비율'] = round(quick_assets / cl.get(yr, 0) * 100, 2)
                    
                    # 현금비율
                    cash = bs_accounts.get('현금및현금성자산', {})
                    if cash and cl and cl.get(yr, 0) != 0:
                        metrics[yr]['현금비율'] = round(cash.get(yr, 0) / cl.get(yr, 0) * 100, 2)
                    
                    # 부채비율
                    liabilities = bs_accounts.get('부채총계', {})
                    equity = bs_accounts.get('자본총계', {})
                    if equity and equity.get(yr, 0) != 0:
                        metrics[yr]['부채비율'] = round(liabilities.get(yr, 0) / equity.get(yr, 0) * 100, 2)
                    
                    # 자기자본비율
                    assets = bs_accounts.get('자산총계', {})
                    if assets and equity and equity.get(yr, 0) != 0:
                        metrics[yr]['자기자본비율'] = round(equity.get(yr, 0) / assets.get(yr, 0) * 100, 2)
                    
                    # 유동부채비율
                    if ca and cl and ca.get(yr, 0) != 0:
                        metrics[yr]['유동부채비율'] = round(cl.get(yr, 0) / ca.get(yr, 0) * 100, 2)
                    
                    # 비유동비율
                    nca = bs_accounts.get('비유동자산', {})
                    if nca and assets and assets.get(yr, 0) != 0:
                        metrics[yr]['비유동자산비율'] = round(nca.get(yr, 0) / assets.get(yr, 0) * 100, 2)
                    
                    # 재고자산비율
                    if inv and ca and ca.get(yr, 0) != 0:
                        metrics[yr]['재고자산비율'] = round(inv.get(yr, 0) / ca.get(yr, 0) * 100, 2)
                    
                    # 매출채권회전율
                    ar = bs_accounts.get('매출채권', {})
                    revenue = is_accounts.get('매출액', {})
                    if ar and revenue and ar.get(yr, 0) != 0:
                        metrics[yr]['매출채권회전율'] = round(revenue.get(yr, 0) / ar.get(yr, 0), 2)
                    
                    # 재고자산회전율
                    cogs = is_accounts.get('매출원가', {})
                    if inv and cogs and inv.get(yr, 0) != 0:
                        metrics[yr]['재고자산회전율'] = round(cogs.get(yr, 0) / inv.get(yr, 0), 2)
                    
                    # 총자산회전율
                    if revenue and assets and assets.get(yr, 0) != 0:
                        metrics[yr]['총자산회전율'] = round(revenue.get(yr, 0) / assets.get(yr, 0), 2)
                
                return metrics
            
            def calculate_is_metrics(is_accounts, years):
                """IS 기반 지표"""
                metrics = {}
                for yr in years:
                    metrics[yr] = {}
                    revenue = is_accounts.get('매출액', {})
                    cogs = is_accounts.get('매출원가', {})
                    gross = is_accounts.get('매출총이익', {})
                    op = is_accounts.get('영업이익', {})
                    net = is_accounts.get('당기순이익', {})
                    
                    # 매출총이익률
                    if gross and revenue and revenue.get(yr, 0) != 0:
                        metrics[yr]['매출총이익률'] = round(gross.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
                    
                    # 판매관리비율
                    sga = is_accounts.get('판매관리비', {})
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
                    
                    # EBITDA이익률
                    if op and revenue and revenue.get(yr, 0) != 0:
                        metrics[yr]['EBITDA마진'] = round(op.get(yr, 0) / revenue.get(yr, 0) * 100, 2)
                    
                    # 비용구조 (판매관리비/매출원가)
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
                """BS + IS 공통 지표"""
                metrics = {}
                for yr in years:
                    metrics[yr] = {}
                    
                    assets = bs_accounts.get('자산총계', {})
                    equity = bs_accounts.get('자본총계', {})
                    liabilities = bs_accounts.get('부채총계', {})
                    revenue = is_accounts.get('매출액', {})
                    net = is_accounts.get('당기순이익', {})
                    op = is_accounts.get('영업이익', {})
                    
                    # ROA (총자산이익률)
                    if net and assets and assets.get(yr, 0) != 0:
                        metrics[yr]['ROA'] = round(net.get(yr, 0) / assets.get(yr, 0) * 100, 2)
                    
                    # ROE (자본이익률)
                    if net and equity and equity.get(yr, 0) != 0:
                        metrics[yr]['ROE'] = round(net.get(yr, 0) / equity.get(yr, 0) * 100, 2)
                    
                    # ROIC (투자자본이익률)
                    cl = bs_accounts.get('유동부채', {})
                    if op and assets and (assets.get(yr, 0) - cl.get(yr, 0)) != 0:
                        ic = assets.get(yr, 0) - cl.get(yr, 0)
                        metrics[yr]['ROIC'] = round(op.get(yr, 0) / ic * 100, 2)
                    
                    # EPS (1株당순이익) - 자본금 필요
                    capital = bs_accounts.get('자본금', {})
                    if capital and net and capital.get(yr, 0) and capital.get(yr, 0) > 0:
                        shares = capital.get(yr, 0) / 1000
                        if shares > 0:
                            metrics[yr]['EPS'] = round(net.get(yr, 0) / shares, 0)
                    
                    # 부채대비현금비율
                    cash = bs_accounts.get('현금및현금성자산', {})
                    if cash and liabilities and liabilities.get(yr, 0) != 0:
                        metrics[yr]['부채대비현금비율'] = round(cash.get(yr, 0) / liabilities.get(yr, 0) * 100, 2)
                    
                    # 이자보상배율
                    opex = is_accounts.get('영업외비용', {})
                    if op and opex and opex.get(yr, 0):
                        metrics[yr]['이자보상배율'] = round(op.get(yr, 0) / abs(opex.get(yr, 0)), 2)
                    
                    # 총자산对企业가치比率
                    if revenue and assets and assets.get(yr, 0) != 0:
                        metrics[yr]['총자산회전율'] = round(revenue.get(yr, 0) / assets.get(yr, 0), 2)
                    
                    # 자본회전율
                    if revenue and equity and equity.get(yr, 0) != 0:
                        metrics[yr]['자본회전율'] = round(revenue.get(yr, 0) / equity.get(yr, 0), 2)
                    
                    # 자산대비이익률
                    if op and assets and assets.get(yr, 0) != 0:
                        metrics[yr]['자산대비영업이익률'] = round(op.get(yr, 0) / assets.get(yr, 0) * 100, 2)
                    
                    # 자본대비이익률
                    if op and equity and equity.get(yr, 0) != 0:
                        metrics[yr]['자본대비영업이익률'] = round(op.get(yr, 0) / equity.get(yr, 0) * 100, 2)
                
                return metrics
            
            # 지표 계산
            bs_metrics = calculate_bs_metrics(bs_accounts, years)
            is_metrics = calculate_is_metrics(is_accounts, years)
            common_metrics = calculate_common_metrics(bs_accounts, is_accounts, years)
            
            # ============ 탭으로 구분하여 표시 ============
            tab_bs_metrics, tab_is_metrics, tab_common = st.tabs(["📊 재무상태표 (BS) 지표", "📈 손익계산서 (IS) 지표", "🔗 공통 지표"])
            
            # BS 지표
            with tab_bs_metrics:
                bs_indicators = ['유동비율', '당좌비율', '현금비율', '부채비율', '자기자본비율', '유동부채비율', '비유동자산비율', '재고자산비율', '매출채권회전율', '재고자산회전율', '총자산회전율']
                bs_df = pd.DataFrame(index=bs_indicators, columns=years)
                for yr in years:
                    for ind in bs_indicators:
                        if bs_metrics[yr].get(ind) is not None:
                            bs_df.loc[ind, yr] = bs_metrics[yr][ind]
                st.dataframe(bs_df.astype(str).replace('nan', '-').replace('None', '-'), use_container_width=True)
            
            # IS 지표
            with tab_is_metrics:
                is_indicators = ['매출총이익률', '판매관리비율', '영업이익률', '순이익률', '매출원가율', 'EBITDA마진', '비용구조비율', '매출액증가율', '총이익증가율', '영업이익증가율', '순이익증가율']
                is_df = pd.DataFrame(index=is_indicators, columns=years)
                for yr in years:
                    for ind in is_indicators:
                        if is_metrics[yr].get(ind) is not None:
                            is_df.loc[ind, yr] = is_metrics[yr][ind]
                st.dataframe(is_df.astype(str).replace('nan', '-').replace('None', '-'), use_container_width=True)
            
            # 공통 지표
            with tab_common:
                common_indicators = ['ROA', 'ROE', 'ROIC', 'EPS', '부채대비현금비율', '이자보상배율', '총자산회전율', '자본회전율', '자산대비영업이익률', '자본대비영업이익률']
                common_df = pd.DataFrame(index=common_indicators, columns=years)
                for yr in years:
                    for ind in common_indicators:
                        if common_metrics[yr].get(ind) is not None:
                            common_df.loc[ind, yr] = common_metrics[yr][ind]
                st.dataframe(common_df.astype(str).replace('nan', '-').replace('None', '-'), use_container_width=True)
            
            # ============ 그래프 시각화 ============
            st.markdown("#### 📈 재무지표 그래프")
            
            # 지표 선택
            all_indicators = bs_indicators + is_indicators + common_indicators
            chart_options = st.multiselect("📊 표시할 지표 선택", all_indicators, default=all_indicators[:6], key="chart_options")
            
            if chart_options:
                import plotly.express as px
                
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
                    fig = px.line(df_chart, x='연도', y='값', color='지표', markers=True)
                    fig.update_layout(title="재무지표 연도별 추이", xaxis_title="연도", yaxis_title="값", legend_title="지표")
                    st.plotly_chart(fig, use_container_width=True)

        # 4. 사전 진단 및 관리 방향성
        st.markdown("---")
        st.markdown("### 4. 사전 진단 및 관리 방향성")
        questions = [
            "재무성과(손익/자금 등) 현황 분석/보고(Report)를 매월 받으십니까?",
            "채권 현황(수금 일정 등)을 정확하게 파악하고 계십니까?",
            "현재 (재고/고정)자산에 대한 장부 가치를 정기적으로 파악하고 계십니까?",
            "원가/비용 등에 대한 내부적인 집행 기준(예산 등)이 수립/공유 되고 있습니까?",
            "연말까지(혹은 3개월 이내) 필요한 자금(유동성)에 대하여 정확히 파악하고 계십니까?",
            "자금(출금)과정에서 용도/금액에 대한 통제 절차가 있습니까?",
            "올해 예상되는 재무성과를 숫자(매출/이익 등)로 산출이 가능합니까?",
            "재무적 비상(리스크) 상황 발생에 대한 내부적인 대응 계획이 수립되어 있습니까?",
            "재무성과는 기업 내의 성과관리지표(KPI/OKR 등)과 연관되어 관리되고 있습니까?",
            "투자 유치 시 우리 기업의 미래 지분 가치를 객관적인 근거로 제시할 수 있습니까?"
        ]
        check_results = [st.radio(f"{i+1}. {q}", ["예", "아니오"], index=1, horizontal=True, key=f"q{i}") for i, q in enumerate(questions)]
        score = check_results.count("예")

        selected_dirs = st.multiselect("◈ 재무관리 방향성", ["안정적 성장", "투자 유치 (사업확장)", "IPO/M&A 등 Exit"], key="sel_dir")
        dir_etc = st.text_input("기타 방향성", value="", key="in_dir_etc")
        selected_mats = st.multiselect("◈ 기타 보유자료", ["사업자등록증", "재무제표", "회사소개서", "기타 양식"], key="sel_mat")

        exec_summary = st.text_area("📑 종합의견 (Executive Summary)", value="", height=150, key="txt_exec")
        finance_comment = st.text_area("💰 재무분석 코멘트", value="", height=100, key="txt_fin")
        account_comment = st.text_area("🔎 세부 계정 분석", value="", key="txt_acc")

        # 5. 보고서 생성 버튼
        st.markdown("---")
        if st.button("🚀 최종 보고서 생성"):
            if not template_file:
                st.error("워드 템플릿 파일을 업로드해 주세요.")
            else:
                # --- [퍼센트 게이지 추가 완료] ---
                progress_text = "데이터를 분석하여 보고서를 생성 중입니다. 잠시만 기다려주세요..."
                my_bar = st.progress(0, text=progress_text)

                for percent_complete in range(100):
                    time.sleep(0.015)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                
                my_bar.empty()
                st.success("🎉 성공적으로 보고서가 완성되었습니다!")
                # ----------------------------------

                doc = DocxTemplate(template_file)
                
                context = {
                    'today': datetime.datetime.now().strftime("%Y. %m."),
                    'company_name': company_name, 
                    'biz_type': biz_type, 
                    'ceo_name': ceo_name,
                    'biz_start_date': biz_start_date, 
                    'biz_no': biz_no, 
                    'phone': phone,
                    'email': full_email, 
                    'address': address, 
                    'emp_count': emp_count,
                    'erp_system': erp_system, 
                    'exec_summary': exec_summary,
                    'finance_comment': finance_comment, 
                    'account_comment': account_comment,
                    'score': score
                }

                # ■ / □ 체크박스 엄격 적용
                for i, res in enumerate(check_results):
                    num = i + 1
                    is_yes = (res == "예")
                    context[f'r{num}y'] = "■" if is_yes else "□"
                    context[f'r{num}n'] = "■" if not is_yes else "□"
                    context[f's{num}y'] = "■" if is_yes else "□"
                    context[f's{num}n'] = "■" if not is_yes else "□"

                # 방향성 체크박스 (안정적 성장, 투자 유치, IPO)
                for i, opt in enumerate(["안정적 성장", "투자 유치 (사업확장)", "IPO/M&A 등 Exit"]):
                    context[f'd{i+1}'] = "■" if opt in selected_dirs else "□"
                
                # 기타 방향성: 체크박스(■/□)와 괄호 안 텍스트 분리
                context['d_etc'] = "■" if dir_etc else "□"
                context['d_etc_val'] = dir_etc if dir_etc else "          "
                
                # 보유자료 체크박스
                for i, opt in enumerate(["사업자등록증", "재무제표", "회사소개서", "기타 양식"]):
                    context[f'm{i+1}'] = "■" if opt in selected_mats else "□"

                doc.render(context)
                output = io.BytesIO()
                doc.save(output)
                
                # 퀵 복사 기능 완전 삭제 완료
                file_name_prefix = company_name if company_name else "진단기업"
                st.download_button(f"📥 {file_name_prefix}_보고서 다운로드", data=output.getvalue(), file_name=f"{file_name_prefix}_재무진단보고서.docx")

        # 6. 하단 기능 버튼
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("🔄 전체 재작성", use_container_width=True):
                st.rerun()
        
        with col_btn2:
            if st.button("🗑️ 모두 지우기", use_container_width=True):
                # 세션 상태 초기화
                for key in st.session_state.keys():
                    if key.startswith(('input_', 'q', 'sel_', 'txt_')):
                        del st.session_state[key]
                st.rerun()
        
        with col_btn3:
            if st.button("🔁 다시 실행하기", use_container_width=True):
                st.rerun()

    # 이 아래의 'except' 구문이 지워져서 났던 에러입니다!
    except Exception as e:
        st.error(f"오류 발생: {e}")
        st.code(traceback.format_exc())