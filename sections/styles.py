"""
전역 디자인 시스템 (CSS) 주입
"""
import streamlit as st


def inject_global_css():
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
