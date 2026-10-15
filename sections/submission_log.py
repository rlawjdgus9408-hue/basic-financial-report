"""
고객용 배포판: 자료 업로드/보고서 생성 시점마다 회사명·연락처·일시를 구글 시트에 기록해
관리자(sections.sidebar._is_admin() 통과자)만 "제출 이력 조회" 패널에서 볼 수 있게 한다.

로컬 JSON/CSV 파일이 아니라 구글 시트에 쓰는 이유: Streamlit Cloud는 재배포/재시작 시
로컬 디스크가 초기화되므로, 로컬 파일로는 기록이 조용히 날아갈 수 있다. 구글 시트는 별도
서버이므로 앱이 몇 번을 재배포돼도 기록이 남는다.

secrets.toml에 필요한 값 (아직 설정 전이어도 앱은 정상 동작하고, 기록/조회만 조용히
비활성화된다 — 업로드·보고서 생성 자체를 막지 않는다):

    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
    client_email = "...@....iam.gserviceaccount.com"
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "..."

    SUBMISSION_SHEET_ID = "구글 시트 ID (시트 URL의 /d/ 와 /edit 사이 문자열)"

주의: 위 service account를 만든 뒤, 기록을 남길 구글 시트를 그 client_email 주소와
"편집자"로 공유해둬야 한다(공유하지 않으면 매 기록 시도가 조용히 실패한다).
"""
import datetime

import streamlit as st

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
_WORKSHEET_NAME = "submissions"
_HEADER = ["일시", "구분", "회사명", "연락처", "이메일"]


def is_configured():
    """구글 시트 연동에 필요한 secrets가 다 채워졌는지 — 로그 기록/조회 UI를 보여줄지 판단용."""
    try:
        return bool(st.secrets.get("gcp_service_account")) and bool(st.secrets.get("SUBMISSION_SHEET_ID"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _client():
    import gspread
    from google.oauth2.service_account import Credentials

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=_SCOPES
    )
    return gspread.authorize(credentials)


def _worksheet():
    sheet_id = st.secrets["SUBMISSION_SHEET_ID"]
    sh = _client().open_by_key(sheet_id)
    try:
        return sh.worksheet(_WORKSHEET_NAME)
    except Exception:
        ws = sh.add_worksheet(title=_WORKSHEET_NAME, rows=1000, cols=len(_HEADER))
        ws.append_row(_HEADER)
        return ws


def log_event(event_type, company_name, phone, email):
    """제출 이력 한 줄을 기록한다. 이 로그는 부가 기능이지 핵심 기능이 아니므로, 시트 미공유나
    네트워크 오류 등으로 기록에 실패해도 예외를 밖으로 던지지 않고 업로드/보고서 생성 자체는
    계속 진행되게 한다(반환값은 성공 여부일 뿐, 호출부에서 반드시 확인할 필요는 없다)."""
    if not is_configured():
        return False
    try:
        _worksheet().append_row([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type,
            company_name or "",
            phone or "",
            email or "",
        ])
        return True
    except Exception:
        return False


@st.cache_data(ttl=30, show_spinner=False)
def fetch_all():
    """관리자 패널 조회용 — 최신 기록이 위로 오도록 반환한다.
    TTL 캐시를 둬 관리자가 패널을 여닫을 때마다 구글 시트 API를 과도하게 호출하지 않는다."""
    if not is_configured():
        return []
    try:
        return list(reversed(_worksheet().get_all_records()))
    except Exception:
        return []
