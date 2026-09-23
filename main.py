"""
그로스파이낸스 기초재무진단 자동화 시스템
메인 실행 파일
"""
import streamlit as st
import streamlit.components.v1 as _components
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

/* Streamlit 아이콘 폰트가 일반 글자로 표시되지 않도록 복원 */
[data-testid="stIconMaterial"], [class*="material-icons"], [class*="material-symbols"] {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                 'Material Icons', sans-serif !important;
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
.stButton > button, [data-testid="stDownloadButton"] > button {
    border-radius: 4px !important;
    font-weight: 600 !important; font-size: 14px !important;
    min-height: 44px !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
.stButton > button[kind="primary"] {
    background-color: #FADB15 !important;
    color: #191919 !important; border: 2px solid #FADB15 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #F0CE00 !important; border-color: #F0CE00 !important;
}
.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #363636 !important; border: 1.5px solid #D5D5D5 !important;
}
.stButton > button[kind="secondary"]:hover {
    background-color: #FAFAFA !important;
    border-color: #FADB15 !important; color: #191919 !important;
}
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
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button p,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button div,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button span {
    text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
    background-color: #FADB15 !important;
    border-color: #FADB15 !important; color: #191919 !important;
}
.stProgress > div > div > div { background-color: #FADB15 !important; }
.stMultiSelect [data-baseweb="tag"] {
    background-color: #FADB15 !important; color: #191919 !important;
}
.stAlert { border-radius: 4px !important; }
.ai-model-label {
    color: #9AA0A6 !important;
    font-size: 11px !important;
    text-align: right !important;
    margin-top: 8px !important;
}

/* 입력창 안쪽 삭제 컨트롤 */
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"][class*="st-key-clear_"]) {
    transform: translateX(-42px) !important;
    margin-left: 0 !important;
    z-index: 5 !important;
    pointer-events: none !important;
}
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"][class*="st-key-clear_"]) button {
    min-height: 0 !important;
    width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
    color: #9AA0A6 !important;
    background: transparent !important;
    border: 0 !important;
    pointer-events: auto !important;
    font-size: 20px !important;
    font-weight: 400 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"][class*="st-key-clear_"]) button:hover {
    color: #191919 !important;
    background: transparent !important;
}

/* ── 업로드 대기 스켈레톤 박스 ── */
.gf-upload-placeholder {
    display: flex; align-items: center; justify-content: center;
    min-height: 160px; border: 1.5px dashed #D9D9D9; border-radius: 8px;
    background: repeating-linear-gradient(135deg, #FAFAFA, #FAFAFA 10px, #F3F3F3 10px, #F3F3F3 20px);
    color: #9AA0A6; font-size: 14px; font-weight: 700; letter-spacing: 0.02em;
    margin-bottom: 14px;
}
.gf-upload-placeholder .gf-dot { animation: gf-blink 1.4s infinite; opacity: 0; }
.gf-upload-placeholder .gf-dot:nth-child(2) { animation-delay: .2s; }
.gf-upload-placeholder .gf-dot:nth-child(3) { animation-delay: .4s; }
@keyframes gf-blink { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }

/* ── 사이드바 하단 고정 진행도 ── */
[class*="st-key-gf_progress_dock"] {
    position: sticky !important; bottom: 0 !important;
    background: #F5F8FA !important;
    padding: 12px 6px 6px !important; margin-top: 16px !important;
    border-top: 1px solid #E8E8E8 !important; z-index: 30 !important;
}
.gf-progress-track {
    width: 100%; height: 8px; background: #E8E8E8; border-radius: 4px;
    overflow: hidden; position: relative;
}
.gf-progress-fill {
    height: 100%; border-radius: 4px; background: linear-gradient(90deg, #FADB15, #F0CE00);
    transition: width .6s cubic-bezier(.22, 1, .36, 1); position: relative; overflow: hidden;
}
.gf-progress-fill::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(120deg, transparent 0%, rgba(255,255,255,.65) 45%, transparent 85%);
    animation: gf-shimmer 1.7s linear infinite;
}
@keyframes gf-shimmer { 0% { transform: translateX(-120%); } 100% { transform: translateX(120%); } }
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

# 사이드바 목차: 클릭 시 해당 단계로 즉시 이동(자유 이동 가능)
STEP_LABELS = [
    "1. 기업 상세 정보 입력",
    "2. 사전 진단 및 관리 방향성",
    "3. 자료 업로드",
    "4. 재무 데이터 검토",
    "5. 종합의견 및 분석 코멘트",
    "6. 최종보고서 생성",
]
TOTAL_WIZARD_STEPS = 5  # 진행도/설문 흐름은 1~5단계 기준 (6단계는 최종 생성 화면)

st.sidebar.markdown('<div style="font-size:11px;font-weight:700;color:#898F91;text-transform:uppercase;letter-spacing:.08em;margin:4px 0 6px;">목차</div>', unsafe_allow_html=True)
for _i, _label in enumerate(STEP_LABELS, start=1):
    _is_active_step = st.session_state.get('current_step', 1) == _i
    if st.sidebar.button(_label, key=f"navbtn_{_i}", use_container_width=True,
                          type="primary" if _is_active_step else "secondary"):
        st.session_state['current_step'] = _i
        st.rerun()
st.sidebar.markdown("---")

if st.sidebar.button("다시 실행", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("임시저장")

# 임시저장: 현재 세션 상태를 JSON으로 다운로드 (버튼/내부 위젯 key 제외)
_skip_types = (bytes, bytearray)
_skip_prefixes = ('btn_', 'sidebar_', 'form_', 'ai_key_', '_load_done_')
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
        if any(_k.startswith(p) for p in ('btn_', 'sidebar_', 'form_', 'ai_key_', '_load_done_')):
            continue
        try:
            st.session_state[_k] = _v
        except Exception:
            pass
    st.session_state['_load_done_' + _load_file.name] = True
    st.sidebar.success("불러오기 완료!")
    st.rerun()

_header_company = st.session_state.get('input_co_name') or st.session_state.get('company_name')
st.title(f"{_header_company + ' ' if _header_company else ''}기초재무진단 보고서")

# 세션 상태 초기화 함수
def init_session_state():
    defaults = {
        'current_step': 1,
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
from sections.info import render_company_info
from sections.upload import render_file_upload
from sections.review import render_data_review
from sections.metrics import render_financial_metrics
from sections.diagnosis import render_diagnosis
from sections.comment import render_comments
from sections.report import render_report_generation

# ── 설문조사형 단계 이동 도우미 ────────────────────────────────────────────────
STEP_INTROS = {
    1: "안녕하세요, 그로스파이낸스입니다 👋<br>기초재무진단보고서 작성을 위한 <b>기본정보</b>를 입력해 주세요.",
    2: "귀사의 현재 재무·경영 관리 수준을 파악하기 위한 <b>설문 단계</b>입니다.<br><br>"
       "1. 각 항목에 대해 <b>예/아니오 중 하나</b>를 선택해 주세요.<br>"
       "2. 재무관리를 하시는 <b>목적(방향성)</b>을 선택해 주시고, 해당 사항이 없다면 <b>기타 항목에 직접 작성</b>해 주세요.<br>"
       "3. 현재 <b>보유하신 회사 자료</b>도 선택해 주세요.",
    3: "<b>표준 재무제표(재무상태표) 및 손익계산서</b> 등의 자료를 업로드해 주세요. "
       "다른 파일 형식이어도 상관없습니다 — AI가 표준 양식으로 자동 변환해 드려요.",
    4: "업로드하신 자료를 바탕으로 자동 추출된 <b>재무 데이터와 지표</b>를 확인해 주세요.",
    5: "마지막 입력 단계입니다! 지금까지의 내용을 바탕으로 <b>종합의견</b>을 작성해 주세요.",
}


def render_step_intro(step):
    text = STEP_INTROS.get(step)
    if not text:
        return
    st.markdown(f"""
    <div style="display:flex; gap:12px; align-items:flex-start;
                background:#FAFAFA; border:1px solid #F0F0F0; border-left:4px solid #FADB15;
                border-radius:0 8px 8px 0; padding:14px 18px; margin-bottom:22px;">
        <div style="flex-shrink:0; width:30px; height:30px; border-radius:50%; background:#FADB15;
                    display:flex; align-items:center; justify-content:center; font-size:15px;">💬</div>
        <div style="font-size:14px; line-height:1.6; color:#363636; padding-top:4px;">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def _progress_message(percent):
    remaining = 100 - percent
    if percent >= 100:
        return "모든 입력이 완료되었습니다! 🎉"
    if percent >= 70:
        return "거의 다 완료했어요! 🙌"
    if percent >= 50:
        return f"절반 넘게 진행했어요! {remaining}% 남았어요"
    if percent > 0:
        return f"{remaining}% 남았어요"
    return "입력을 시작해 주세요"


def render_sidebar_progress(step, total=TOTAL_WIZARD_STEPS):
    """사이드바 하단에 고정(sticky)되는 애니메이션 진행도 바.
    (본문 하단 고정은 사이드바의 '보고서 생성' 버튼 등과 겹치는 문제가 있어,
     겹침 없이 항상 보이는 사이드바 하단 고정 방식을 사용한다.)
    진행도는 '완료한 단계' 기준이므로 현재 단계 진입 시점에는 아직 반영하지 않는다.
    (예: 1단계 진입 시 0% → 1단계를 마치고 2단계로 넘어가면 20%)"""
    percent = int(round((step - 1) / total * 100))
    message = _progress_message(percent)
    with st.sidebar.container(key="gf_progress_dock"):
        st.markdown(f"""
        <div style="font-size:11px; font-weight:700; color:#9AA0A6; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px;">진행도</div>
        <div style="font-size:12px; font-weight:600; color:#363636; margin-bottom:7px;">{message}</div>
        <div class="gf-progress-track">
            <div class="gf-progress-fill" style="width:{percent}%;"></div>
        </div>
        <div style="text-align:right; font-size:11px; color:#9AA0A6; margin-top:5px;">{step} / {total} 단계 · {percent}%</div>
        """, unsafe_allow_html=True)


def render_upload_placeholder(tab_labels=None, height=160):
    """자료 업로드 전, 실제 표/지표가 나올 자리를 채우는 스켈레톤 placeholder."""
    def _box():
        st.markdown(f"""
        <div class="gf-upload-placeholder" style="min-height:{height}px;">
            <span>Uploading<span class="gf-dot">.</span><span class="gf-dot">.</span><span class="gf-dot">.</span></span>
        </div>
        """, unsafe_allow_html=True)

    if tab_labels:
        for tab in st.tabs(tab_labels):
            with tab:
                _box()
    else:
        _box()


def render_step_nav(step, total=TOTAL_WIZARD_STEPS):
    col_prev, col_next = st.columns([1, 2])
    with col_prev:
        if step > 1:
            if st.button("← 이전 단계", key=f"btn_prev_{step}", use_container_width=True):
                st.session_state['current_step'] = step - 1
                st.rerun()
    with col_next:
        next_label = "다음 단계로 →" if step < total else "입력 완료, 보고서 생성하러 가기 →"
        if st.button(next_label, key=f"btn_next_{step}", type="primary", use_container_width=True):
            st.session_state['current_step'] = step + 1
            st.rerun()


# Default values so every variable is defined regardless of which step is active
company_info = {}
template_file = None
check_results = []
score = 0
selected_dirs = []
dir_etc = ''
selected_mats = []
uploaded_file = None
df_bs = df_is = None
years = []
exec_summary = st.session_state.get('txt_exec', st.session_state.get('exec_summary', ''))

current_step = st.session_state.get('current_step', 1)

# 현재 단계만 화면에 보이도록 나머지 단계 컨테이너를 CSS로 숨긴다.
# (모든 단계의 렌더 함수는 매 실행마다 호출되어 데이터 연속성을 유지한다)
_hide_css = "\n".join(f'.st-key-step{_n} {{ display: none !important; }}' for _n in range(1, 7) if _n != current_step)
st.markdown(f"<style>{_hide_css}</style>", unsafe_allow_html=True)

# 진행도는 사이드바 하단에 고정 표시 (1~5단계 설문 흐름에서만, 6단계 제외)
if 1 <= current_step <= TOTAL_WIZARD_STEPS:
    render_sidebar_progress(current_step)

# 1. 기업 상세 정보 입력
with st.container(key="step1"):
    render_step_intro(1)
    company_info = render_company_info()
    render_step_nav(1)

# 2. 사전 진단 및 관리 방향성
with st.container(key="step2"):
    render_step_intro(2)
    check_results, score, selected_dirs, dir_etc, selected_mats = render_diagnosis()
    render_step_nav(2)

# 3. 자료 업로드
with st.container(key="step3"):
    render_step_intro(3)
    uploaded_file, template_file, df_bs, df_is, years = render_file_upload()
    render_step_nav(3)

# 4. 재무 데이터 검토
with st.container(key="step4"):
    render_step_intro(4)
    if uploaded_file and df_bs is not None and df_is is not None:
        render_data_review(df_bs, df_is)

        # 4-1. 재무지표 연도별 추이
        bs_metrics, is_metrics, common_metrics, years = render_financial_metrics(df_bs, df_is, years)

        # 세션에 지표 데이터 저장 (section5에서 사용)
        st.session_state['bs_metrics'] = bs_metrics
        st.session_state['is_metrics'] = is_metrics
        st.session_state['common_metrics'] = common_metrics
        st.session_state['years'] = years
    else:
        st.markdown("### 4. 재무 데이터 검토")
        st.caption("자료를 업로드하면 이 자리에 재무상태표·손익계산서와 지표가 표시됩니다.")
        render_upload_placeholder(["🏛️ 재무상태표 (BS)", "📈 손익계산서 (IS)"])
        st.markdown("### 4-1. 재무지표 연도별 추이")
        render_upload_placeholder()
    render_step_nav(4)

# 5. 종합의견
with st.container(key="step5"):
    render_step_intro(5)
    exec_summary = render_comments()
    render_step_nav(5)

# 6. 최종보고서 생성 (설문 흐름/진행도에는 포함되지 않는 완료 화면)
with st.container(key="step6"):
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
    if st.button("← 이전 단계(종합의견 수정)", key="btn_prev_6"):
        st.session_state['current_step'] = 5
        st.rerun()

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
        created_date = datetime.datetime.now().strftime('%Y%m%d')
        st.session_state['report_filename'] = f"{file_name_prefix}_재무진단보고서_{created_date}.docx"
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