"""
Section 4 보조: 계정별 AI 코멘트 자동 생성 (고객용 자동분석 파이프라인 전용)

업로드된 재무상태표/손익계산서 원본 계정(df_bs/df_is)을 근거로, anthropic-skills:기초재무진단
스킬의 Q2(계정 선정)·Q3(계정별 코멘트) 규칙에 따라 핵심 계정을 추려 색상 판단(Level)과
40자 이내 코멘트를 한 번의 Claude 호출로 받는다. 결과는 report.py가 실제 Word 표로 렌더링한다.
"""
import re

from sections.ai_client import (
    anthropic_client, skill_text, app_rule_text, ACCOUNT_COMMENT_SKILL_FILES, AUTO_PIPELINE_PREAMBLE,
)
from sections.convert import _is_transient_error, _MAX_RETRIES

_ACCOUNT_COMMENT_MAX_CHARS = 40  # 스킬 Q3-1 출력 형식
_INDICATOR_COMMENT_MAX_CHARS = 50  # 스킬 Q4-2 출력 형식

_COLOR_HEX = {
    "sky": "DAEEF3",
    "gray": "F2F2F2",
    "orange": "FDE9D9",
}

_TOOL_NAME = "record_account_comments"

_ACCOUNT_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "account": {"type": "string"},
        "level": {"type": "integer", "enum": [1, 2, 3]},
        "color": {"type": "string", "enum": ["sky", "gray", "orange"]},
        "comment": {"type": "string"},
    },
    "required": ["account", "level", "color", "comment"],
}

_SCHEMA = {
    "type": "object",
    "properties": {
        "bs_accounts": {"type": "array", "items": _ACCOUNT_ITEM_SCHEMA, "maxItems": 20},
        "is_accounts": {"type": "array", "items": _ACCOUNT_ITEM_SCHEMA, "maxItems": 20},
        # 지표(비율)는 이미 선정이 끝난 고정 목록이라 account 필드에 지표명을 그대로 담는다
        # (계정과 같은 스키마를 재사용 — report.py 렌더링 쪽에서도 item["account"]로 읽는다).
        "bs_indicators": {"type": "array", "items": _ACCOUNT_ITEM_SCHEMA, "maxItems": 20},
        "is_indicators": {"type": "array", "items": _ACCOUNT_ITEM_SCHEMA, "maxItems": 20},
    },
    "required": ["bs_accounts", "is_accounts", "bs_indicators", "is_indicators"],
}

_ARROW_RATIO_PATTERN = re.compile(r"\([^)]*%\s*→\s*[^)]*%[^)]*\)")

# 전 연도 값이 0이어도 걸러내지 않는 필수 묶음 — Q2 선정 기준의 "총계류/매출액" 등.
_MANDATORY_KEYWORDS = ["총계", "자본금", "매출액"]


def _df_to_text(df, years, title):
    lines = [f"[{title}]", "계정과목\t" + "\t".join(years)]
    for _, row in df.iterrows():
        values = "\t".join(str(row.get(y, "")) for y in years)
        lines.append(f"{row['계정과목']}\t{values}")
    return "\n".join(lines)


def _indicator_rows_to_text(rows, years, title):
    if not rows:
        return f"[{title}]\n(해당 없음)"
    lines = [f"[{title}]", "지표명\t" + "\t".join(years)]
    for r in rows:
        lines.append(r.get("지표명", "") + "".join(f"\t{r.get(y, '-')}" for y in years))
    return "\n".join(lines)


def generate_account_comments(api_key, model, df_bs, df_is, years, bs_indicator_rows=None, is_indicator_rows=None,
                              company_context=""):
    """df_bs/df_is 전체 계정 데이터를 근거로 Claude가 핵심 계정을 선정하고 색상·코멘트를
    매기는 동시에, 이미 선정이 끝난 지표(bs_indicator_rows/is_indicator_rows — build_indicator_table
    결과를 BS/IS로 나눈 것)에도 같은 규칙으로 코멘트를 붙인다. company_context(기업명·업종 등)는
    스킬의 산업 특성 판단에 쓰도록 프롬프트 앞에 붙인다. 반환값:
    {'bs_accounts','is_accounts','bs_indicators','is_indicators','warnings'} — 각 항목은
    {'account','level','color','color_hex','comment'} 딕셔너리.

    convert.py::_extract_financial_data와 같은 방식으로 503/529류 일시 과부하에는 재시도한다."""
    client = anthropic_client(api_key)

    prompt = f"""[기업 정보]
{company_context or "(제공되지 않음)"}

아래 재무상태표/손익계산서 전체 계정 데이터를 근거로, 핵심 계정을 선정해
색상 판단(Level)과 코멘트를 작성하세요(bs_accounts/is_accounts). 연도는 왼쪽이 오래된 연도,
오른쪽이 최신 연도입니다.

중요: 각 항목의 account 필드는 아래 데이터에 있는 계정과목 표기를 한 글자도 바꾸지 말고
정확히 그대로 사용하세요(보고서에서 이 값으로 원본 행을 다시 찾아 연도별 금액을 붙입니다 —
표기가 조금이라도 다르면 그 계정의 금액이 빠집니다).

{_df_to_text(df_bs, years, "재무상태표")}

{_df_to_text(df_is, years, "손익계산서")}

그리고 아래 지표(비율)는 이미 보고서에 넣을 항목으로 선정이 끝났으니, 추가 선정이나 제외
없이 전부에 대해 같은 규칙(색상 판단 4단계, Level, 명사형 코멘트, 50자 이내)으로 코멘트를
작성하세요(bs_indicators/is_indicators). account 필드에는 지표명을 그대로 쓰세요.
값의 단위: 비율·증가율은 %, 회수기간·회전일수·결제기간·현금전환주기는 일, 이자보상배율은 배입니다.

{_indicator_rows_to_text(bs_indicator_rows, years, "재무상태표 관련 지표")}

{_indicator_rows_to_text(is_indicator_rows, years, "손익계산서 관련 지표")}
"""
    tool = {
        "name": _TOOL_NAME,
        "description": "선정된 핵심 계정·지표별 Level·색상·코멘트를 기록한다.",
        "input_schema": _SCHEMA,
    }

    import time as _time

    system = "\n\n".join([
        AUTO_PIPELINE_PREAMBLE,
        "[계정·지표 코멘트 규칙 — 스킬 원문]",
        skill_text(ACCOUNT_COMMENT_SKILL_FILES),
        app_rule_text("account_comment_guideline.md"),
    ])

    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=16000,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                tools=[tool],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                messages=[{"role": "user", "content": prompt}],
            )
            # 길이 제한에 걸리면 도구 입력이 중간에 잘려 계정이 일부 빠진 채로 들어올 수 있다.
            if response.stop_reason == "max_tokens":
                raise RuntimeError("계정별 코멘트 응답이 길이 제한(max_tokens)에 걸려 중간에 끊겼습니다")
            tool_block = next((b for b in response.content if b.type == "tool_use"), None)
            if tool_block is None:
                raise RuntimeError(f"계정별 코멘트 결과를 받지 못했습니다 (stop_reason={response.stop_reason})")
            result = tool_block.input
            bs_accounts = _attach_hex(_drop_zero_accounts(result.get("bs_accounts", []), df_bs, years))
            is_accounts = _attach_hex(_drop_zero_accounts(result.get("is_accounts", []), df_is, years))
            bs_indicators = _attach_hex(result.get("bs_indicators", []))
            is_indicators = _attach_hex(result.get("is_indicators", []))
            warnings = (
                _check_rules(bs_accounts, "재무상태표", _ACCOUNT_COMMENT_MAX_CHARS)
                + _check_rules(is_accounts, "손익계산서", _ACCOUNT_COMMENT_MAX_CHARS)
                + _check_rules(bs_indicators, "재무상태표 지표", _INDICATOR_COMMENT_MAX_CHARS)
                + _check_rules(is_indicators, "손익계산서 지표", _INDICATOR_COMMENT_MAX_CHARS)
            )
            return {
                "bs_accounts": bs_accounts,
                "is_accounts": is_accounts,
                "bs_indicators": bs_indicators,
                "is_indicators": is_indicators,
                "warnings": warnings,
            }
        except Exception as error:
            last_error = error
            if not _is_transient_error(error) or attempt == _MAX_RETRIES - 1:
                raise
            _time.sleep(3 * (attempt + 1))
    raise last_error


def _drop_zero_accounts(items, df, years):
    """프롬프트로 '0값 비필수 계정 제외'를 지시해도 모델이 가끔 넣는 경우가 있어, 안전망으로
    코드에서도 한 번 더 거른다 — df에서 해당 계정의 전 연도 값이 0이고 필수 묶음도 아니면
    뺀다. df에서 못 찾으면(표기 불일치) 판단 근거가 없으므로 그대로 둔다."""
    if df is None:
        return items
    kept = []
    for item in items:
        account = item.get("account", "")
        if any(k in account for k in _MANDATORY_KEYWORDS):
            kept.append(item)
            continue
        match = df[df["계정과목"] == account]
        if match.empty:
            kept.append(item)
            continue
        row = match.iloc[0]
        values = [row.get(y, 0) for y in years]
        if any(v not in (0, "0", None) for v in values):
            kept.append(item)
    return kept


def _attach_hex(items):
    for item in items:
        item["color_hex"] = _COLOR_HEX.get(item.get("color"), _COLOR_HEX["gray"])
    return items


def _check_rules(items, statement_name, max_chars):
    """가벼운 규칙 점검 — 위반해도 생성 자체는 막지 않고 경고만 돌려준다
    (고객용 흐름은 사람이 다시 검토하는 화면이 없어, ES 품질 검사(_quick_style_check)와
    같은 '경고만 표시' 철학을 그대로 따른다)."""
    warnings = []
    arrow_count = sum(1 for item in items for _ in _ARROW_RATIO_PATTERN.finditer(item.get("comment", "")))
    if arrow_count > 2:
        warnings.append(f"{statement_name} 코멘트에 화살표 비율 표기가 {arrow_count}개로 규칙(최대 2개)을 초과했습니다.")
    for item in items:
        comment = item.get("comment", "")
        if len(comment) > max_chars:
            warnings.append(
                f"{statement_name} '{item.get('account')}' 코멘트가 {len(comment)}자로 {max_chars}자를 초과했습니다."
            )
    return warnings
