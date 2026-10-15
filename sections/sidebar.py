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
_SKIP_PREFIXES = ('btn_', 'sidebar_', 'form_', 'ai_key_', '_load_done_')


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
    버튼과 같은 기준(wizard.max_reachable_step)을 공유해 두 경로 모두 막는다."""
    from sections.wizard import max_reachable_step
    reachable = max_reachable_step()

    st.sidebar.markdown(
        '<div style="font-size:11px;font-weight:700;color:#898F91;text-transform:uppercase;'
        'letter-spacing:.08em;margin:4px 0 6px;">목차</div>',
        unsafe_allow_html=True
    )
    for i, label in enumerate(STEP_LABELS, start=1):
        is_active = st.session_state.get('current_step', 1) == i
        is_locked = i > reachable
        if st.sidebar.button(
            f"🔒 {label}" if is_locked else label,
            key=f"navbtn_{i}", use_container_width=True,
            type="primary" if is_active else "secondary",
            disabled=is_locked,
            help="이전 단계의 필수 항목을 먼저 채워주세요." if is_locked else None,
        ):
            st.session_state['current_step'] = i
            st.rerun()
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


def _is_admin():
    """고객용 배포판은 실제 외부 고객이 들어오는 화면이라, 운영 점검 도구(API 키 확인 등)를
    아무나 보게 두면 키 등록 여부·끝자리가 노출되고 '연결 테스트' 버튼으로 누구나 과금되는
    Gemini API 호출을 트리거할 수 있다. secrets.toml에 ADMIN_TOKEN을 설정하고 그 값을
    ?admin=<토큰> 쿼리파라미터로 넘겼을 때만 통과시킨다 — 토큰 미설정 시 기본값은 '막음'이다."""
    try:
        admin_token = st.secrets.get("ADMIN_TOKEN", "")
    except Exception:
        admin_token = ""
    if not admin_token:
        return False
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


def render_sidebar_chrome():
    """사이드바 상단 공통 영역: 제목 + 목차 + 다시 실행 + 임시저장/불러오기 + API 키 확인"""
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
