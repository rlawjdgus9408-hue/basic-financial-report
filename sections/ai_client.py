"""
공통 Gemini API 설정/연동 유틸리티 (comment.py, convert.py 공용)
"""
import json
import os
from pathlib import Path

import streamlit as st

_CONFIG_FILE = Path(__file__).parent.parent / "config.json"
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
