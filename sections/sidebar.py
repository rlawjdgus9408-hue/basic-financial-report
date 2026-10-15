"""
사이드바 공통 UI: 제목, 접힘 방지, 목차 이동, 다시 실행, 임시저장/불러오기
"""
import json
import datetime

import streamlit as st
import streamlit.components.v1 as components

STEP_LABELS = [
    "1. 기업 상세 정보 입력",
    "2. 사전 진단 및 관리 방향성",
    "3. 자료 업로드",
    "4. 최종보고서 생성",
]

_SKIP_TYPES = (bytes, bytearray)
# '_'로 시작하는 키는 전부 내부용 임시 상태(관리자 로그인 비밀번호 입력값, 네비게이션 경고
# 플래그 등)로 취급해 "임시저장" JSON에 담지 않는다 — 특히 관리자 비밀번호 입력창(위젯 키
# _admin_login_pw)이 평문으로 다운로드 파일에 남는 것을 막기 위함.
_SKIP_PREFIXES = ('btn_', 'sidebar_', 'form_', 'ai_key_', '_')


def _keep_sidebar_open():
    """사이드바 강제 표시 유지 (접기 방지)"""
    components.html("""
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


def _render_step_nav():
    """목차: 완료한 단계까지는 자유롭게 이동할 수 있지만, 필수 항목(1단계 신원 정보,
    2단계 사전진단)이 비어있는 단계보다 뒤로는 못 건너뛴다. 이 제한이 없으면 1단계를
    비워둔 채 목차에서 곧장 "3. 자료 업로드"나 "4. 최종보고서 생성"으로 이동해, 신원
    확인 없이 AI 호출(비용 발생)을 돌릴 수 있게 된다 — render_step_nav의 '다음 단계'
    버튼과 같은 기준(wizard.max_reachable_step)을 공유해 두 경로 모두 막는다.

    버튼을 잠가두는 대신(자물쇠 아이콘 없이) 항상 클릭 가능하게 두고, 막힌 단계를 눌렀을
    때만 그 자리에서 경고를 보여준다 — render_step_nav의 '다음 단계' 버튼과 동일하게
    "시도했을 때만 안내" 방식으로 통일."""
    from sections.wizard import max_reachable_step, step_missing_items, is_step_complete
    reachable = max_reachable_step()
    warn_key = '_nav_sidebar_warn_step'

    blocking_step = st.session_state.get(warn_key)
    if blocking_step and is_step_complete(blocking_step):
        st.session_state.pop(warn_key, None)

    st.sidebar.markdown(
        '<div style="font-size:11px;font-weight:700;color:#898F91;text-transform:uppercase;'
        'letter-spacing:.08em;margin:4px 0 6px;">목차</div>',
        unsafe_allow_html=True
    )
    for i, label in enumerate(STEP_LABELS, start=1):
        is_active = st.session_state.get('current_step', 1) == i
        if st.sidebar.button(label, key=f"navbtn_{i}", use_container_width=True,
                              type="primary" if is_active else "secondary"):
            if i <= reachable:
                st.session_state.pop(warn_key, None)
                st.session_state['current_step'] = i
                st.rerun()
            else:
                st.session_state[warn_key] = reachable

    blocking_step = st.session_state.get(warn_key)
    if blocking_step:
        missing = step_missing_items(blocking_step)
        st.sidebar.warning(f"⚠️ {blocking_step}단계의 필수 항목을 먼저 채워주세요: " + ", ".join(missing))
    st.sidebar.markdown("---")


def _render_temp_save_load():
    """임시저장: 현재 세션 상태를 JSON으로 다운로드 (버튼/내부 위젯 key 제외) / 불러오기"""
    st.sidebar.subheader("임시저장")

    save_state = {}
    for k, v in st.session_state.items():
        if isinstance(v, (_SKIP_TYPES, bool)):  # 불리언은 버튼 상태 — 저장 불필요
            continue
        if any(k.startswith(p) for p in _SKIP_PREFIXES):
            continue
        try:
            json.dumps(v)
            save_state[k] = v
        except (TypeError, ValueError):
            pass

    company_label = st.session_state.get('input_co_name') or st.session_state.get('company_name') or '진단기업'
    st.sidebar.download_button(
        "임시저장 다운로드",
        data=json.dumps(save_state, ensure_ascii=False, indent=2).encode('utf-8'),
        file_name=f"{company_label}_임시저장_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True,
        key="sidebar_save_btn"
    )

    load_file = st.sidebar.file_uploader(
        "📂 불러오기 (.json)", type=["json"], key="sidebar_load_file", label_visibility="collapsed"
    )
    if load_file is not None and not st.session_state.get('_load_done_' + load_file.name):
        loaded = json.loads(load_file.read().decode('utf-8'))
        for k, v in loaded.items():
            if isinstance(v, bool):
                continue
            if any(k.startswith(p) for p in _SKIP_PREFIXES):
                continue
            try:
                st.session_state[k] = v
            except Exception:
                pass
        st.session_state['_load_done_' + load_file.name] = True
        st.sidebar.success("불러오기 완료!")
        st.rerun()


def _admin_token():
    try:
        return st.secrets.get("ADMIN_TOKEN", "")
    except Exception:
        return ""


def _is_admin():
    """고객용 배포판은 실제 외부 고객이 들어오는 화면이라, 운영 점검 도구(API 키 확인 등)를
    아무나 보게 두면 키 등록 여부·끝자리가 노출되고 '연결 테스트' 버튼으로 누구나 과금되는
    Gemini API 호출을 트리거할 수 있다. secrets.toml에 ADMIN_TOKEN을 설정해둬야만 통과하는
    게 기본 원칙(미설정 시 항상 막음)이고, 통과하는 경로는 두 가지다:
    (1) ?admin=<토큰> 쿼리파라미터, (2) 사이드바 맨 아래 "🔐 관리자" 로그인(같은 토큰을
    비밀번호로 입력) — 로그인에 성공하면 세션 동안 _admin_authenticated로 기억해 매번
    URL을 붙이지 않아도 된다."""
    admin_token = _admin_token()
    if not admin_token:
        return False
    if st.session_state.get("_admin_authenticated"):
        return True
    try:
        query_token = st.query_params.get("admin", "")
    except Exception:
        query_token = st.experimental_get_query_params().get("admin", [""])[0]
    return query_token == admin_token


def _render_api_key_check():
    """배포 환경(Streamlit Cloud Secrets)에 Gemini API 키가 제대로 들어갔는지 바로 확인하는 도구.
    파일 업로드까지 가지 않아도 키 등록 여부/실제 호출 가능 여부를 바로 알 수 있게 한다.
    _is_admin()을 통과한 경우에만 호출되므로 일반 방문자에게는 보이지 않는다."""
    from sections.ai_client import configured_value, gemini_model

    with st.sidebar.expander("⚙️ API 키 확인"):
        api_key = configured_value("Gemini", "api_key")
        if not api_key:
            st.error("GEMINI_API_KEY가 설정되지 않았습니다.")
            return

        st.caption(f"키 등록됨 (...{api_key[-4:]})")
        if st.button("연결 테스트", key="btn_api_key_test", use_container_width=True):
            model = gemini_model()
            with st.spinner("Gemini API 호출 테스트 중..."):
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    client.models.generate_content(model=model, contents="ping")
                    st.success(f"연결 성공! (모델: {model})")
                except Exception as error:
                    st.error(f"연결 실패: {error}")


def _render_submission_log():
    """자료 업로드/보고서 생성 시점마다 쌓인 제출 이력(회사명·연락처·일시)을 조회하는 패널.
    _is_admin()을 통과한 경우에만 호출되므로 일반 방문자에게는 보이지 않는다."""
    from sections import submission_log

    with st.sidebar.expander("📋 제출 이력 조회"):
        if not submission_log.is_configured():
            st.caption("구글 시트 연동이 설정되지 않았습니다 (secrets.toml의 gcp_service_account / "
                       "SUBMISSION_SHEET_ID 확인 필요).")
            return

        if st.button("새로고침", key="btn_submission_log_refresh", use_container_width=True):
            submission_log.fetch_all.clear()

        rows = submission_log.fetch_all()
        if not rows:
            st.caption("아직 기록된 제출 이력이 없습니다.")
            return

        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_admin_login():
    """메뉴 맨 아래의 "🔐 관리자" — URL에 ?admin=토큰을 매번 붙이지 않아도, 비밀번호(=
    ADMIN_TOKEN)만 입력하면 그 자리에서 관리자 모드를 켤 수 있게 한다. 암호를 모르는 일반
    방문자에게는 로그인 입력창만 보이고, 그 안의 운영 정보(API 키 확인·제출 이력)는 로그인에
    성공해야만 드러난다 — ADMIN_TOKEN이 아예 설정돼 있지 않으면 이 항목 자체를 숨긴다."""
    if not _admin_token():
        return

    if st.session_state.get("_admin_authenticated"):
        with st.sidebar.expander("🔓 관리자 모드 (로그인됨)"):
            if st.button("로그아웃", key="btn_admin_logout", use_container_width=True):
                st.session_state.pop("_admin_authenticated", None)
                st.rerun()
        return

    with st.sidebar.expander("🔐 관리자"):
        pw = st.text_input(
            "관리자 비밀번호", type="password", key="_admin_login_pw",
            placeholder="비밀번호 입력", label_visibility="collapsed",
        )
        if st.button("로그인", key="btn_admin_login", use_container_width=True):
            if pw and pw == _admin_token():
                st.session_state["_admin_authenticated"] = True
                st.session_state.pop("_admin_login_pw", None)
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")


def render_sidebar_chrome():
    """사이드바 상단 공통 영역: 제목 + 목차 + 다시 실행 + 임시저장/불러오기 + (로그인 시) API 키
    확인·제출 이력 + 맨 아래 관리자 로그인"""
    st.sidebar.title("메뉴")
    st.sidebar.markdown("---")

    _keep_sidebar_open()
    _render_step_nav()

    if st.sidebar.button("다시 실행", use_container_width=True):
        st.rerun()

    st.sidebar.markdown("---")
    _render_temp_save_load()

    if _is_admin():
        st.sidebar.markdown("---")
        _render_api_key_check()
        _render_submission_log()

    st.sidebar.markdown("---")
    _render_admin_login()
