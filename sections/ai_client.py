"""
공통 Claude API 설정/연동 유틸리티 (comment.py, convert.py, auto_pipeline.py 등 공용)
"""
import json
import os
import re
from pathlib import Path

import streamlit as st

_CONFIG_FILE = Path(__file__).parent.parent / "config.json"
_DOCS_DIR = Path(__file__).parent.parent / "docs"
# Claude Code 스킬 원문(anthropic-skills:기초재무진단, executive-summary)을 그대로 둔 폴더.
# 스킬이 갱신되면 이 폴더 파일만 교체한다.
_SKILLS_DIR = Path(__file__).parent.parent / "skills"

# 작업별로 시스템 지시문에 넣을 스킬 파일. 기초재무진단 SKILL.md의 STEP별 "읽을 파일" 안내를
# 따르되, 엑셀 산출물·RAW·Mode B 비교처럼 이 앱에서 하지 않는 단계의 파일은 넣지 않는다.
# ES는 SKILL.md 5장 미해결 과제의 제안대로 executive-summary를 기준본으로 두고, 기초재무진단에만
# 있는 Q5-13~Q5-20(es-verification.md)을 보탠다.
ES_SKILL_FILES = (
    "executive-summary/SKILL.md",
    "기초재무진단/references/es-verification.md",
    "기초재무진단/references/writing-rules.md",
)
ACCOUNT_COMMENT_SKILL_FILES = (
    "기초재무진단/references/statements-and-accounts.md",
    "기초재무진단/references/account-comments.md",
    "기초재무진단/references/writing-rules.md",
)

# 스킬 원문은 사람이 Claude Code에서 대화하며 쓰는 전제로 쓰여 있어("사용자에게 묻는다",
# "스크립트를 돌린다", "엑셀 시트" 등), 사람이 개입하지 않는 자동 파이프라인에서는 그 지시를
# 어떻게 읽어야 하는지 먼저 알려준다.
AUTO_PIPELINE_PREAMBLE = """[자동 실행 안내]
아래 규칙 문서는 Claude Code에서 사람과 대화하며 쓰는 스킬 원문이다. 이번 요청은 사람이 중간에
확인하지 않는 자동 생성이므로 다음과 같이 적용한다.
- 사용자에게 질문하거나 확인을 요청하지 않는다. 확인할 수 없는 사항은 추정하지 말고 쓰지 않거나 '확인 불가'로 둔다.
- 스크립트 실행, 파일 열기·저장, 엑셀(Graph·Analysis·RAW 시트) 작성 지시는 이번 요청에 해당하지 않으므로 건너뛴다.
- 규칙 문서의 '보고서 지면'(Analysis 노출 행·코멘트·지표·사전 검토사항)은 이번 요청에 함께 전달되는 표와 응답을 뜻한다.
- 기준자료(재무지표 기준값표·산업별 참조표·성장단계표)는 제공되지 않는다. 스킬에 적힌 기준으로 판단하고, 기준값표 등급 명칭이나 성장단계(Lv)를 지어내지 않는다.
- 결과물 본문만 출력한다."""

_ENV_KEY_NAME = "ANTHROPIC_API_KEY"
_WORKSPACE_ENV_KEY_NAME = "ANTHROPIC_WORKSPACE_ID"
_DEFAULT_MODEL = "claude-sonnet-5"


@st.cache_data(show_spinner=False, max_entries=1)
def _load_config(mtime):
    """config.json을 파싱해 캐시한다. 파일이 바뀌면(mtime 변경) 캐시가 자동 무효화된다.
    (인자 이름에 밑줄을 붙이면 Streamlit이 캐시 키 계산에서 그 인자를 제외해버리므로,
    무효화 트리거로 쓸 이 값은 반드시 밑줄 없이 넘겨야 한다.)"""
    try:
        return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _config():
    try:
        mtime = _CONFIG_FILE.stat().st_mtime
    except OSError:
        return {}
    return _load_config(mtime)


def configured_value(provider, key):
    """config.json 또는 환경변수/Streamlit secrets에서 설정값을 읽는다.

    이 앱은 단계마다 전체 스크립트가 재실행되는 마법사 구조라, 이 함수는 위젯 클릭 한 번마다
    반복 호출된다. config.json 파싱 결과를 캐시해 매번 디스크를 다시 읽지 않게 한다."""
    if key == "api_key":
        try:
            secret_value = st.secrets.get(_ENV_KEY_NAME, "")
        except Exception:
            secret_value = ""
        return secret_value or os.getenv(_ENV_KEY_NAME, "")

    config = _config()
    for model_config in config.get("models", []):
        if model_config.get("provider", "").lower() == provider.lower():
            return model_config.get(key, "")
    return ""


def ai_model():
    """설정된 모델명을 반환하되, Claude 모델명이 아니면(예: 옛 config.json에 남은 gemini 모델명)
    기본 모델로 대체한다."""
    configured_model = configured_value("Claude", "model")
    if not configured_model.startswith("claude-"):
        return _DEFAULT_MODEL
    return configured_model


def ai_api_key():
    return configured_value("Claude", "api_key")


def ai_workspace_id():
    """개인(사용자) 범위 API 키(sk-ant-usr-...)는 anthropic-workspace-id 헤더 없이는 호출이
    거부된다. 워크스페이스 전용 키(sk-ant-api03-...)를 쓰면 비워둬도 된다."""
    try:
        secret_value = st.secrets.get(_WORKSPACE_ENV_KEY_NAME, "")
    except Exception:
        secret_value = ""
    return secret_value or os.getenv(_WORKSPACE_ENV_KEY_NAME, "")


def anthropic_client(api_key):
    """워크스페이스 ID가 설정돼 있으면 anthropic-workspace-id 헤더를 자동으로 붙인 클라이언트를
    만든다 (comment.py/convert.py/auto_pipeline.py/sidebar.py 공용)."""
    import anthropic

    workspace_id = ai_workspace_id()
    default_headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
    return anthropic.Anthropic(api_key=api_key, default_headers=default_headers)


def generate_text(api_key, model, system_instruction, prompt, max_tokens=8192):
    """Claude에 텍스트 전용 프롬프트를 보내고 답변 텍스트만 돌려준다
    (comment.py의 대화형 질문-답변, auto_pipeline.py의 자동 종합의견 생성이 공용으로 사용).

    thinking을 명시적으로 꺼둔다 — Claude 5 계열은 기본적으로 답변 전에 내부 'thinking'
    토큰을 쓰는데 이것도 max_tokens에 포함돼서, 복잡한 재무 데이터 프롬프트에서는 thinking만
    하다 토큰이 바닥나 본문 텍스트가 0자로 끝나는 경우가 있었다. ES/채팅 답변은 정해진 규칙을
    따르는 정형 텍스트 생성이라 깊은 추론이 필요 없어, thinking을 꺼서 토큰 예산을 안정적으로
    쓰는 쪽이 낫다. 혹시라도 텍스트가 비면(다른 원인으로) 빈 문자열로 조용히 넘기지 않고
    예외를 던져서(호출부의 재시도/에러 처리로 이어지게), '응답을 받지 못했습니다' 같은 가짜
    성공 결과가 보고서에 그대로 박히는 사고를 막는다."""
    client = anthropic_client(api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        # 시스템 지시문(스킬 원문, 수천 토큰)은 매 호출 같으므로 캐시해 반복 비용을 줄인다.
        system=[{"type": "text", "text": system_instruction, "cache_control": {"type": "ephemeral"}}],
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude 응답이 길이 제한(max_tokens)에 걸려 중간에 끊겼습니다")
    text = "".join(block.text for block in response.content if block.type == "text")
    if not text:
        raise RuntimeError(f"Claude가 본문 텍스트를 생성하지 못했습니다 (stop_reason={response.stop_reason})")
    return text


_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


@st.cache_data(show_spinner=False, max_entries=8)
def _load_skill_files(paths, mtimes):
    """mtimes는 캐시 무효화 키로만 쓴다(파일이 바뀌면 다시 읽는다)."""
    parts = []
    for rel in paths:
        text = (_SKILLS_DIR / rel).read_text(encoding="utf-8")
        # SKILL.md 맨 위 YAML 머리말(name/description)은 Claude Code가 스킬을 고를 때 쓰는
        # 트리거 문구라 지시문으로는 군더더기다.
        parts.append(f"<!-- {rel} -->\n" + _FRONTMATTER_RE.sub("", text.replace("\r\n", "\n")).strip())
    return "\n\n".join(parts)


def skill_text(paths):
    """skills/ 폴더의 스킬 원문 파일들을 이어붙여 시스템 지시문으로 쓸 텍스트를 만든다.
    스킬을 고치면 skills/ 아래 파일만 교체하면 된다(코드 수정 불필요).

    파일이 하나라도 없으면 빈 문자열로 조용히 넘기지 않고 예외를 던진다 — 규칙 없이
    생성된 결과가 그대로 보고서에 들어가는 것보다 생성 실패로 드러나는 편이 낫다."""
    paths = tuple(paths)
    mtimes = tuple((_SKILLS_DIR / rel).stat().st_mtime for rel in paths)
    return _load_skill_files(paths, mtimes)


def ai_comment_extra_rules():
    """config.json의 'ai_comment_rules' 필드 — ES 가이드라인 외에 추가로 항상 지켜야 할
    임시/보조 규칙을 코드 수정 없이 넣고 싶을 때 사용한다 (선택 사항, 비워두면 무시됨)."""
    return (_config().get("ai_comment_rules") or "").strip()


def app_rule_text(filename):
    """docs/ 아래 앱 전용 보충 규칙(스킬 원문을 이 앱의 출력 형식에 맞추는 부분)을 읽는다."""
    return (_DOCS_DIR / filename).read_text(encoding="utf-8")
