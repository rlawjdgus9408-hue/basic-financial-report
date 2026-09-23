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


def configured_value(provider, key):
    """config.json 또는 환경변수/Streamlit secrets에서 설정값을 읽는다."""
    if key == "api_key":
        try:
            secret_value = st.secrets.get(_ENV_KEY_NAME, "")
        except Exception:
            secret_value = ""
        return secret_value or os.getenv(_ENV_KEY_NAME, "")

    try:
        config = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        for model_config in config.get("models", []):
            if model_config.get("provider", "").lower() == provider.lower():
                return model_config.get(key, "")
    except (OSError, json.JSONDecodeError):
        pass
    return ""


def gemini_model():
    """설정된 모델명을 반환하되, 지원 종료된 구형 모델명이면 기본 모델로 대체한다."""
    configured_model = configured_value("Gemini", "model")
    if configured_model in _LEGACY_MODELS:
        return _DEFAULT_GEMINI_MODEL
    return configured_model


def gemini_api_key():
    return configured_value("Gemini", "api_key")


def es_guideline_text():
    """Executive Summary(종합의견) 작성 규칙 전문을 읽어온다.
    docs/es_guideline.md 파일만 고치면 코드 수정 없이 바로 반영된다."""
    try:
        return _ES_GUIDELINE_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""


def ai_comment_extra_rules():
    """config.json의 'ai_comment_rules' 필드 — ES 가이드라인 외에 추가로 항상 지켜야 할
    임시/보조 규칙을 코드 수정 없이 넣고 싶을 때 사용한다 (선택 사항, 비워두면 무시됨)."""
    try:
        config = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        return (config.get("ai_comment_rules") or "").strip()
    except (OSError, json.JSONDecodeError):
        return ""
