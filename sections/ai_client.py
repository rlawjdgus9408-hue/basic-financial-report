"""
공통 Gemini API 설정/연동 유틸리티 (comment.py, convert.py 공용)
"""
import json
import os
from pathlib import Path

import streamlit as st

_CONFIG_FILE = Path(__file__).parent.parent / "config.json"
_ES_GUIDELINE_FILE = Path(__file__).parent.parent / "docs" / "es_guideline.md"
_ENV_KEY_NAME = "GEMINI_API_KEY"
_DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
_LEGACY_MODELS = {"", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-flash"}


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


def gemini_model():
    """설정된 모델명을 반환하되, 지원 종료된 구형 모델명이면 기본 모델로 대체한다."""
    configured_model = configured_value("Gemini", "model")
    if configured_model in _LEGACY_MODELS:
        return _DEFAULT_GEMINI_MODEL
    return configured_model


def gemini_api_key():
    return configured_value("Gemini", "api_key")


@st.cache_data(show_spinner=False, max_entries=1)
def _load_es_guideline(mtime):
    try:
        return _ES_GUIDELINE_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""


def es_guideline_text():
    """Executive Summary(종합의견) 작성 규칙 전문을 읽어온다.
    docs/es_guideline.md 파일만 고치면 코드 수정 없이 바로 반영된다(파일이 바뀌면 캐시도 갱신됨)."""
    try:
        mtime = _ES_GUIDELINE_FILE.stat().st_mtime
    except OSError:
        return ""
    return _load_es_guideline(mtime)


def ai_comment_extra_rules():
    """config.json의 'ai_comment_rules' 필드 — ES 가이드라인 외에 추가로 항상 지켜야 할
    임시/보조 규칙을 코드 수정 없이 넣고 싶을 때 사용한다 (선택 사항, 비워두면 무시됨)."""
    return (_config().get("ai_comment_rules") or "").strip()
