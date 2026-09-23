"""
전역 디자인 시스템 (CSS) 주입
"""
import streamlit as st


def inject_global_css():
    st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');

/* ── 다크 테마 팔레트 (강조색인 노란색 계열은 그대로 유지) ──
   BG_MAIN #0D0D0D · BG_ELEVATED #1A1A1A · BG_ELEVATED_2 #161616
   BORDER #2A2A2A · BORDER_STRONG #3A3A3A
   TEXT_PRIMARY #F2F2F2 · TEXT_SECONDARY #D0D0D0 · TEXT_MUTED #9AA0A6 */

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
.stApp { background-color: #0D0D0D; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1080px; }

/* ── 제목 ── */
h1 {
    font-size: 26px !important; font-weight: 800 !important;
    color: #F2F2F2 !important;
    padding-bottom: 14px !important;
    border-bottom: 3px solid #FADB15 !important;
    margin-bottom: 30px !important;
}

/* ── 섹션 헤더 (h3) ── */
h3 {
    font-size: 16px !important; font-weight: 700 !important;
    color: #F2F2F2 !important;
    padding: 10px 14px !important;
    border-left: 4px solid #FADB15 !important;
    background-color: #1A1A1A !important;
    border-radius: 0 4px 4px 0 !important;
    margin: 28px 0 18px 0 !important;
}

/* ── 라벨 ── */
label p, .stTextInput label p, .stSelectbox label p,
.stTextArea label p, .stMultiSelect label p {
    font-size: 13px !important; font-weight: 600 !important;
    color: #D0D0D0 !important; margin-bottom: 4px !important;
}

/* ── 텍스트에어리어 줄간격 ── */
textarea { line-height: 1.7 !important; }

/* ── 구분선 ── */
hr { border: none !important; border-top: 1.5px solid #2A2A2A !important; margin: 28px 0 !important; }

/* ── 캡션 ── */
.stCaption p, small { color: #9AA0A6 !important; font-size: 12px !important; }
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
    background-color: #1E1E1E !important;
    color: #E5E5E5 !important; border: 1.5px solid #3A3A3A !important;
}
.stButton > button[kind="secondary"]:hover {
    background-color: #262626 !important;
    border-color: #FADB15 !important; color: #FFFFFF !important;
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
    background-color: #161616 !important;
    border-right: 1px solid #2A2A2A !important;
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
    color: #F2F2F2 !important; border: none !important;
    padding: 0 !important; margin-bottom: 10px !important;
}
[data-testid="stSidebar"] h3 {
    font-size: 11px !important; font-weight: 700 !important;
    color: #9AA0A6 !important; border: none !important;
    background: none !important; padding: 0 !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important;
    margin: 14px 0 6px 0 !important;
}
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
    min-height: 40px !important; font-size: 13px !important;
    font-weight: 500 !important; background-color: #1E1E1E !important;
    color: #E0E0E0 !important; border: 1px solid #2E2E2E !important;
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

/* ── 입력창(텍스트/텍스트에어리어/셀렉트박스): 어두운 페이지 위에서도 잘 보이도록
   흰 배경 카드로 표시한다. (표/데이터에디터는 캔버스로 직접 그려서 CSS로 못 바꾼다 —
   앱 전체를 밝은 테마로 바꾸지 않는 한 표만 따로 밝게 할 방법이 없다.) ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #191919 !important;
    border: 1px solid #D5D5D5 !important;
}
[data-baseweb="select"] input { color: #191919 !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #9AA0A6 !important;
}
/* 셀렉트박스를 열었을 때 뜨는 옵션 목록(팝오버)도 같이 흰 배경으로 */
[data-baseweb="popover"] [data-baseweb="menu"], ul[role="listbox"] {
    background-color: #FFFFFF !important;
}
[data-baseweb="menu"] li, ul[role="listbox"] li,
[data-baseweb="menu"] li *, ul[role="listbox"] li * {
    color: #191919 !important;
}
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
    color: #FADB15 !important;
    background: transparent !important;
}

/* ── 업로드 대기 스켈레톤 박스 ── */
.gf-upload-placeholder {
    display: flex; align-items: center; justify-content: center;
    min-height: 160px; border: 1.5px dashed #3A3A3A; border-radius: 8px;
    background: repeating-linear-gradient(135deg, #161616, #161616 10px, #1C1C1C 10px, #1C1C1C 20px);
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
    background: #161616 !important;
    padding: 12px 6px 6px !important; margin-top: 16px !important;
    border-top: 1px solid #2A2A2A !important; z-index: 30 !important;
}
.gf-progress-track {
    width: 100%; height: 8px; background: #2A2A2A; border-radius: 4px;
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
