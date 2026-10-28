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
    system = "\n\n".join([
        AUTO_PIPELINE_PREAMBLE,
        "[계정·지표 코멘트 규칙 — 스킬 원문]",
        skill_text(ACCOUNT_COMMENT_SKILL_FILES),
        app_rule_text("account_comment_guideline.md"),
    ])

    result = _request_comments(client, model, system, tool, prompt)
    bs_accounts = _snap_to_source_labels(result.get("bs_accounts", []), df_bs)
    is_accounts = _snap_to_source_labels(result.get("is_accounts", []), df_is)

    # 스킬 Q2-1 필수 묶음은 존재하면 반드시 포함해야 하는데 AI가 가끔 빠뜨린다(시뮬레이션에서
    # 단기·장기대여금 누락 확인). 코드로 원본에 있는 필수 계정을 찾아, 빠진 것만 한 번 더 요청해 채운다.
    missing_bs = _missing_mandatory(bs_accounts, df_bs, years, _MANDATORY_BS)
    missing_is = _missing_mandatory(is_accounts, df_is, years, _MANDATORY_IS)
    warnings = []
    if missing_bs or missing_is:
        supplement_prompt = f"""{prompt}
[추가 요청 — 필수 계정 누락 보완]
아래 계정은 스킬 Q2-1 숨김 불가 필수 묶음인데 앞선 선정에서 빠졌습니다. 이 계정들에 대해서만
같은 규칙으로 Level·색상·코멘트를 작성하세요. account 필드는 아래 표기를 그대로 씁니다.
지표(bs_indicators/is_indicators)는 빈 목록으로 둡니다.
- 재무상태표: {", ".join(missing_bs) or "(없음)"}
- 손익계산서: {", ".join(missing_is) or "(없음)"}

이미 작성된 다른 계정 코멘트(같은 수치를 반복하지 않도록 참고):
{_comments_to_text(bs_accounts + is_accounts)}"""
        try:
            extra = _request_comments(client, model, system, tool, supplement_prompt)
            bs_accounts += [i for i in _snap_to_source_labels(extra.get("bs_accounts", []), df_bs)
                            if i.get("account") in missing_bs]
            is_accounts += [i for i in _snap_to_source_labels(extra.get("is_accounts", []), df_is)
                            if i.get("account") in missing_is]
        except Exception as error:
            warnings.append(f"필수 계정 보완 요청 실패: {error}")
        still_missing = (_missing_mandatory(bs_accounts, df_bs, years, _MANDATORY_BS)
                         + _missing_mandatory(is_accounts, df_is, years, _MANDATORY_IS))
        if still_missing:
            warnings.append(f"스킬 Q2-1 필수 계정이 보고서에서 빠졌습니다: {', '.join(still_missing)}")

    bs_accounts = _attach_hex(_sort_by_source(_drop_zero_accounts(bs_accounts, df_bs, years), df_bs))
    is_accounts = _attach_hex(_sort_by_source(_drop_zero_accounts(is_accounts, df_is, years), df_is))
    bs_indicators = _attach_hex(result.get("bs_indicators", []))
    is_indicators = _attach_hex(result.get("is_indicators", []))
    warnings += (
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


def _request_comments(client, model, system, tool, prompt):
    """코멘트 도구 호출 한 번. 503/529류 일시 과부하에는 재시도하고, 응답이 길이 제한에 걸려
    잘렸거나 도구 결과가 없으면 예외를 던진다(계정이 일부 빠진 채로 조용히 넘어가지 않게)."""
    import time as _time

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
            if response.stop_reason == "max_tokens":
                raise RuntimeError("계정별 코멘트 응답이 길이 제한(max_tokens)에 걸려 중간에 끊겼습니다")
            tool_block = next((b for b in response.content if b.type == "tool_use"), None)
            if tool_block is None:
                raise RuntimeError(f"계정별 코멘트 결과를 받지 못했습니다 (stop_reason={response.stop_reason})")
            return tool_block.input
        except Exception as error:
            if not _is_transient_error(error) or attempt == _MAX_RETRIES - 1:
                raise
            _time.sleep(3 * (attempt + 1))


def _comments_to_text(items):
    return "\n".join(f"- {i.get('account')}: {i.get('comment')}" for i in items) or "(없음)"


# 스킬 Q2-1 숨김 불가 필수 묶음 — (찾을 패턴, 제외 패턴). 원본에 있고 금액이 있으면 반드시 들어가야 한다.
# 패턴마다 재무제표 순서상 처음 걸리는 행(= 상위 행)을 필수 계정으로 본다.
_MANDATORY_BS = [
    ("유동자산", "비유동"), ("비유동자산", None), ("자산총계", None),
    ("유동부채", "비유동"), ("비유동부채", None), ("부채총계", None),
    ("자본금", None), ("이익잉여금|결손금", None), ("자본총계", "부채"),
    ("현금", None), ("단기금융|단기예금|단기투자", None),
    ("매출채권", None), ("재고자산", None), ("매입채무", None),
    ("단기차입금", None), ("장기차입금", "유동성"),
    ("가지급금", None), ("단기대여금", None), ("장기대여금", None),
]
_MANDATORY_IS = [
    ("매출액", None), ("이자비용", None), ("당기순", None),
]


def _missing_mandatory(items, df, years, groups):
    """원본(df)에 있는 필수 계정 중 items(선정 결과)에 빠진 계정의 원본 표기 목록."""
    if df is None:
        return []
    labels = df["계정과목"].astype(str)
    usable = ~labels.str.contains("률|%|/", na=False)
    selected = {i.get("account") for i in items}
    missing = []
    for pattern, exclude in groups:
        hit = usable & labels.str.contains(pattern, na=False)
        if exclude:
            hit &= ~labels.str.contains(exclude, na=False)
        if not hit.any():
            continue
        row = df[hit].iloc[0]
        has_value = any(row.get(y) not in (0, "0", None, "") and row.get(y) == row.get(y) for y in years)
        if has_value and row["계정과목"] not in selected and row["계정과목"] not in missing:
            missing.append(row["계정과목"])
    return missing


def _sort_by_source(items, df):
    """보고서 표가 재무제표 순서를 따르도록 원본 행 순서로 정렬한다(원본에 없는 이름은 맨 뒤)."""
    if df is None:
        return items
    order = {label: i for i, label in enumerate(df["계정과목"].astype(str))}
    return sorted(items, key=lambda item: order.get(item.get("account"), len(order)))


# 계정명 앞 번호(Ⅰ. / I. / 1. / (2) / 가.)와 공백·괄호·기호 — 원본 표기와 AI 표기를 비교할 때 무시한다.
_LABEL_PREFIX_RE = re.compile(r"^\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|[IVX]+\.|\(\d+\)|\d+\.|[가-하]\.)")
_LABEL_NOISE_RE = re.compile(r"[\s()（）\[\]+～~·․.,]")


def _normalize_label(label):
    return _LABEL_NOISE_RE.sub("", _LABEL_PREFIX_RE.sub("", str(label)))


def _snap_to_source_labels(items, df):
    """AI가 계정명을 원본과 조금 다르게 적는 경우가 있다(예: "자본총계(Ⅲ+～Ⅶ)" → "자본총계(Ⅲ～Ⅶ)",
    "2.단기차입금" → "1.단기차입금"). 그러면 보고서가 원본 행을 못 찾아 금액이 '-'로 빠지므로,
    정확히 일치하지 않는 이름은 번호·공백·기호를 뺀 형태로 다시 비교해 원본 표기로 바꿔 둔다.
    그래도 못 찾으면 그대로 둔다."""
    if df is None:
        return items
    labels = [str(v) for v in df["계정과목"]]
    exact = set(labels)
    by_norm = {}
    for label in labels:
        by_norm.setdefault(_normalize_label(label), label)  # 같은 이름이 여럿이면 재무제표 순서상 첫 행
    for item in items:
        account = item.get("account", "")
        if account not in exact:
            item["account"] = by_norm.get(_normalize_label(account), account)
    return items


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
