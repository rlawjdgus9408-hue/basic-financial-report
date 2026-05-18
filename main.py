"""
그로스파이낸스 기초재무진단 자동화 시스템
메인 실행 파일
"""
import streamlit as st
import streamlit.components.v1 as _components
import pandas as pd
import io
import json
import time
import datetime
from docxtpl import DocxTemplate

# 페이지 설정
st.set_page_config(page_title="그로스파이낸스 재무진단 시스템", layout="wide", initial_sidebar_state="expanded")

# ── 디자인 시스템 ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');

/* ── 글꼴 전역 적용 ── */
html, body, [class*="css"], * {
    font-family: 'Pretendard Variable', Pretendard, -apple-system,
                 BlinkMacSystemFont, 'Apple SD Gothic Neo', sans-serif !important;
}

/* ── 기본 레이아웃 ── */
#MainMenu, footer, header { visibility: hidden; }
.stApp { background-color: #FFFFFF; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1080px; }

/* ── 제목 ── */
h1 {
    font-size: 26px !important; font-weight: 800 !important;
    color: #191919 !important;
    padding-bottom: 14px !important;
    border-bottom: 3px solid #FADB15 !important;
    margin-bottom: 30px !important;
}

/* ── 섹션 헤더 (h3) ── */
h3 {
    font-size: 16px !important; font-weight: 700 !important;
    color: #212121 !important;
    padding: 10px 14px !important;
    border-left: 4px solid #FADB15 !important;
    background-color: #FAFAFA !important;
    border-radius: 0 4px 4px 0 !important;
    margin: 28px 0 18px 0 !important;
}

/* ── 라벨 ── */
label p, .stTextInput label p, .stSelectbox label p,
.stTextArea label p, .stMultiSelect label p {
    font-size: 13px !important; font-weight: 600 !important;
    color: #363636 !important; margin-bottom: 4px !important;
}

/* ── 텍스트에어리어 줄간격 ── */
textarea { line-height: 1.7 !important; }

/* ── 구분선 ── */
hr { border: none !important; border-top: 1.5px solid #F0F0F0 !important; margin: 28px 0 !important; }

/* ── 캡션 ── */
.stCaption p, small { color: #898F91 !important; font-size: 12px !important; }

/* ── 버튼 공통 ── */
.stButton > button, [data-testid="stDownloadButton"] > button {
    border-radius: 4px !important;
    font-weight: 600 !important; font-size: 14px !important;
    min-height: 44px !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}

/* ── Primary 버튼 (선택됨) ── */
.stButton > button[kind="primary"] {
    background-color: #FADB15 !important;
    color: #191919 !important; border: 2px solid #FADB15 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #F0CE00 !important; border-color: #F0CE00 !important;
}

/* ── Secondary 버튼 ── */
.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #363636 !important; border: 1.5px solid #D5D5D5 !important;
}
.stButton > button[kind="secondary"]:hover {
    background-color: #FAFAFA !important;
    border-color: #FADB15 !important; color: #191919 !important;
}

/* ── 예/아니오 답변 버튼 (진단 섹션) ── */
[data-testid="stHorizontalBlock"] .stButton > button {
    min-height: 58px !important;
    font-size: 15px !important; letter-spacing: 0.03em !important;
}

/* ── 사이드바 (항상 표시 + 스타일) ── */
[data-testid="stSidebar"] {
    transform: translateX(0) !important;
    display: flex !important;
    visibility: visible !important;
    min-width: 240px !important;
    background-color: #F5F8FA !important;
    border-right: 1px solid #E8E8E8 !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"], button[aria-label="Open sidebar"],
button[title="Collapse sidebar"], button[title="Expand sidebar"],
section[data-testid="stSidebar"] > div > div > button {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    font-size: 15px !important; font-weight: 700 !important;
    color: #212121 !important; border: none !important;
    padding: 0 !important; margin-bottom: 10px !important;
}
[data-testid="stSidebar"] h3 {
    font-size: 11px !important; font-weight: 700 !important;
    color: #898F91 !important; border: none !important;
    background: none !important; padding: 0 !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important;
    margin: 14px 0 6px 0 !important;
}
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
    min-height: 40px !important; font-size: 13px !important;
    font-weight: 500 !important; background-color: #FFFFFF !important;
    color: #363636 !important; border: 1px solid #E0E0E0 !important;
    border-radius: 4px !important; margin-bottom: 3px !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button p {
    text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
    background-color: #FADB15 !important;
    border-color: #FADB15 !important; color: #191919 !important;
}

/* ── 프로그레스바 ── */
.stProgress > div > div > div { background-color: #FADB15 !important; }

/* ── 멀티셀렉트 태그 ── */
.stMultiSelect [data-baseweb="tag"] {
    background-color: #FADB15 !important; color: #191919 !important;
}

/* ── 알림 박스 ── */
.stAlert { border-radius: 4px !important; }
</style>
""", unsafe_allow_html=True)

# 사이드바 생성
st.sidebar.title("메뉴")
st.sidebar.markdown("---")

# 사이드바 강제 표시 유지 (접기 방지)
_components.html("""
<script>
(function keepSidebarOpen() {
    function forceOpen() {
        var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.setProperty('transform', 'translateX(0)', 'important');
            sidebar.style.setProperty('visibility', 'visible', 'important');
            sidebar.style.setProperty('display', 'flex', 'important');
        }
        ['collapsedControl','stSidebarCollapseButton'].forEach(function(id) {
            var el = window.parent.document.querySelector('[data-testid="' + id + '"]');
            if (el) el.style.setProperty('display', 'none', 'important');
        });
    }
    forceOpen();
    var observer = new MutationObserver(forceOpen);
    observer.observe(window.parent.document.body, {
        attributes: true, subtree: true, attributeFilter: ['style','class']
    });
})();
</script>
""", height=0)

# 네비게이션 링크
nav_items = [
    ("1. 기업 상세 정보 입력", "sec1"),
    ("2. 사전 진단 및 관리 방향성", "sec2"),
    ("3. 자료 업로드", "sec3"),
    ("4. 재무 데이터 검토", "sec4"),
    ("5. 종합의견 및 분석 코멘트", "sec5"),
    ("6. 최종보고서 생성", "sec6"),
]

for label, key in nav_items:
    if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
        st.session_state['nav_target'] = key
        st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("작업")

if st.sidebar.button("모두 지우기", use_container_width=True):
    st.rerun()

if st.sidebar.button("다시 실행", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("임시저장")

# 임시저장: 현재 세션 상태를 JSON으로 다운로드 (버튼/내부 위젯 key 제외)
_skip_types = (bytes, bytearray)
_skip_prefixes = ('btn_', 'sidebar_', 'form_', '_load_done_')
_save_state = {}
for _k, _v in st.session_state.items():
    if isinstance(_v, (_skip_types, bool)):  # 불리언은 버튼 상태 — 저장 불필요
        continue
    if any(_k.startswith(p) for p in _skip_prefixes):
        continue
    try:
        json.dumps(_v)
        _save_state[_k] = _v
    except (TypeError, ValueError):
        pass

_company_label = st.session_state.get('input_co_name') or st.session_state.get('company_name') or '진단기업'
st.sidebar.download_button(
    "임시저장 다운로드",
    data=json.dumps(_save_state, ensure_ascii=False, indent=2).encode('utf-8'),
    file_name=f"{_company_label}_임시저장_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
    mime="application/json",
    use_container_width=True,
    key="sidebar_save_btn"
)

# 불러오기: JSON 파일 업로드로 세션 상태 복원
_load_file = st.sidebar.file_uploader("📂 불러오기 (.json)", type=["json"], key="sidebar_load_file", label_visibility="collapsed")
if _load_file is not None and not st.session_state.get('_load_done_' + _load_file.name):
    _loaded = json.loads(_load_file.read().decode('utf-8'))
    for _k, _v in _loaded.items():
        if isinstance(_v, bool):
            continue
        if any(_k.startswith(p) for p in ('btn_', 'sidebar_', 'form_', '_load_done_')):
            continue
        try:
            st.session_state[_k] = _v
        except Exception:
            pass
    st.session_state['_load_done_' + _load_file.name] = True
    st.sidebar.success("불러오기 완료!")
    st.rerun()

st.title("그로스파이낸스 기초재무진단 보고서")

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
        'special_note': '',
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# 각 섹션 import
from section1_info import render_company_info
from section2_upload import render_file_upload
from section3_review import render_data_review
from section3_1_metrics import render_financial_metrics
from section4_diagnosis import render_diagnosis
from section5_comment import render_comments
from section6_report import render_report_generation

def _clear_nav():
    st.session_state['nav_target'] = ''


# Default values so every variable is defined regardless of which nav branch runs
company_info = {}
template_file = None
check_results = []
score = 0
selected_dirs = []
dir_etc = ''
selected_mats = []

# If a nav target is set, render only that section (quick jump view).
nav_target = st.session_state.get('nav_target', '')
if nav_target:
    st.sidebar.button("전체보기", on_click=_clear_nav, use_container_width=True)
    if nav_target == 'sec1':
        company_info = render_company_info()
    elif nav_target == 'sec2':
        check_results, score, selected_dirs, dir_etc, selected_mats = render_diagnosis()
    elif nav_target == 'sec3':
        uploaded_file, template_file, df_bs, df_is, years = render_file_upload()
    elif nav_target == 'sec4':
        # requires uploaded data
        uploaded_file, template_file, df_bs, df_is, years = render_file_upload()
        if uploaded_file and df_bs is not None and df_is is not None:
            render_data_review(df_bs, df_is)
            bs_metrics, is_metrics, common_metrics, years = render_financial_metrics(df_bs, df_is, years)
    elif nav_target == 'sec5':
        exec_summary = render_comments()
    elif nav_target == 'sec6':
        st.markdown('### 6. 최종보고서 생성')
        st.info("보고서 생성은 사이드바의 '보고서 생성' 버튼을 사용하세요.")

else:
    # 1. 기업 상세 정보 입력
    company_info = render_company_info()

    st.markdown("---")

    # 2. 사전 진단 및 관리 방향성
    check_results, score, selected_dirs, dir_etc, selected_mats = render_diagnosis()

    st.markdown("---")

    # 3. 자료 업로드
    uploaded_file, template_file, df_bs, df_is, years = render_file_upload()

    if uploaded_file and df_bs is not None and df_is is not None:
        # 4. 재무 데이터 검토
        render_data_review(df_bs, df_is)
        
        # 4-1. 재무지표 연도별 추이
        bs_metrics, is_metrics, common_metrics, years = render_financial_metrics(df_bs, df_is, years)
        
        # 세션에 지표 데이터 저장 (section5에서 사용)
        st.session_state['bs_metrics'] = bs_metrics
        st.session_state['is_metrics'] = is_metrics
        st.session_state['common_metrics'] = common_metrics
        st.session_state['years'] = years

# 5. 종합의견
st.markdown('<div id="sec5"></div>', unsafe_allow_html=True)
exec_summary = render_comments()

st.markdown("---")

# 6. 최종보고서 생성
st.markdown('<div id="sec6"></div>', unsafe_allow_html=True)
render_report_generation(
    company_info=company_info,
    template_file=template_file,
    check_results=check_results,
    score=score,
    selected_dirs=selected_dirs,
    dir_etc=dir_etc,
    selected_mats=selected_mats,
    exec_summary=exec_summary,
)

# 사이드바 보고서 생성 (모든 변수가 정의된 후 실행)
st.sidebar.markdown("---")
st.sidebar.subheader("최종보고서")

if template_file:
    if st.sidebar.button("보고서 생성", use_container_width=True):
        progress_text = "데이터를 분석하여 보고서를 생성 중입니다. 잠시만 기다려주세요..."
        my_bar = st.sidebar.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.015)
            my_bar.progress(percent_complete + 1, text=progress_text)

        my_bar.empty()

        doc = DocxTemplate(template_file)

        context = {
            'today': datetime.datetime.now().strftime("%Y. %m."),
            'company_name': company_info.get('company_name', ''),
            'biz_type': company_info.get('biz_type', ''),
            'ceo_name': company_info.get('ceo_name', ''),
            'biz_start_date': company_info.get('biz_start_date', ''),
            'biz_no': company_info.get('biz_no', ''),
            'phone': company_info.get('phone', ''),
            'email': company_info.get('email', ''),
            'address': company_info.get('address', ''),
            'emp_count': company_info.get('emp_count', ''),
            'erp_system': ', '.join(company_info.get('erp_system', [])) if isinstance(company_info.get('erp_system'), list) else company_info.get('erp_system', ''),
            'special_note': company_info.get('special_note', ''),
            'exec_summary': exec_summary,
            'finance_comment': st.session_state.get('selected_indicators_table', ''),
            'score': score
        }

        for i, res in enumerate(check_results):
            num = i + 1
            is_yes = (res == "예")
            context[f'r{num}y'] = "■" if is_yes else "□"
            context[f'r{num}n'] = "■" if not is_yes else "□"
            context[f's{num}y'] = "■" if is_yes else "□"
            context[f's{num}n'] = "■" if not is_yes else "□"

        for i, opt in enumerate(["안정적 성장", "투자 유치 (사업확장)", "IPO/M&A 등 Exit"]):
            context[f'd{i+1}'] = "■" if opt in selected_dirs else "□"

        context['d_etc'] = "■" if dir_etc else "□"
        context['d_etc_val'] = dir_etc if dir_etc else "          "

        for i, opt in enumerate(["사업자등록증", "재무제표", "회사소개서", "기타 양식"]):
            context[f'm{i+1}'] = "■" if opt in selected_mats else "□"

        doc.render(context)
        output = io.BytesIO()
        doc.save(output)

        file_name_prefix = company_info.get('company_name', '') or "진단기업"
        st.session_state['report_bytes'] = output.getvalue()
        st.session_state['report_filename'] = f"{file_name_prefix}_재무진단보고서.docx"
        st.session_state['report_company'] = file_name_prefix
        st.sidebar.success("보고서 생성 완료!")

    if st.session_state.get('report_bytes'):
        file_name_prefix = st.session_state.get('report_company', '진단기업')
        st.sidebar.download_button(
            f"{file_name_prefix} 보고서 다운로드",
            data=st.session_state['report_bytes'],
            file_name=st.session_state['report_filename'],
            use_container_width=True
        )