"""
RAW 시트 입력(raw_input.json) 검증 스크립트.
.claude/skills/raw-sheet/SKILL.md §6 검증 항목을 구현한다.

사용법:
    python scripts/check_raw.py raw_input.json

종료 코드: ERROR가 하나라도 있으면 1, 없으면 0 (WARN만 있어도 0).

스크립트가 못 잡는 것(§6 하단 참고): 원본에 있는데 JSON에 아예 없는 계정.
합계가 맞아도 세부 계정 하나를 빼고 다른 계정에 금액을 합쳐 넣었으면 통과한다.
"""
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

_LABEL_PREFIX_RE = re.compile(
    r"^\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX]+\.?|\d+\.|\(\d+\)|[①②③④⑤⑥⑦⑧⑨⑩]|[가-힣]\.)\s*"
)
TOLERANCE = 1  # 원 단위 반올림 오차 허용


def normalize(name):
    """로마자/번호/가나다 접두어를 제거해 핵심 계정명만 남긴다 (sections/raw_template.py와 동일 규칙)."""
    text = str(name or "").strip()
    while True:
        new_text = _LABEL_PREFIX_RE.sub("", text, count=1).strip()
        if new_text == text:
            break
        text = new_text
    return text


def _close(a, b, tol=TOLERANCE):
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def check_structure(data, report):
    years = data.get("years") or []
    if not years:
        report.error("최상위 'years' 배열이 비어 있습니다.")
        return
    if not data.get("statements"):
        report.error("'statements' 배열이 비어 있습니다.")
        return

    for stmt in data.get("statements", []):
        title = stmt.get("title", "(제목 없음)")
        seen_names = {}
        for i, row in enumerate(stmt.get("rows", [])):
            name = (row.get("name") or "").strip()
            if not name:
                report.error(f"[{title}] {i}번째 행의 계정명이 비어 있습니다.")
            elif name in seen_names:
                report.error(f"[{title}] 계정명 중복: '{name}' ({seen_names[name]}번째, {i}번째 행)")
            else:
                seen_names[name] = i

            level = row.get("level")
            if level is None or not isinstance(level, int) or not (0 <= level <= 4):
                report.error(f"[{title}] '{name}' 의 level 값이 올바르지 않습니다: {level!r} (0~4 범위 정수여야 함)")

            values = row.get("values")
            if values is None:
                if not row.get("note"):
                    report.error(f"[{title}] '{name}' 에 values가 없고 note(확인 불가 사유)도 없습니다 (§5).")
                continue
            if len(values) != len(years):
                report.error(
                    f"[{title}] '{name}' 의 values 길이({len(values)})가 years 길이({len(years)})와 다릅니다."
                )


def _row_index(stmt_rows, keywords, level_max=None):
    """정규화한 계정명이 keywords 중 하나와 정확히 일치하는 첫 행의 인덱스를 찾는다."""
    for i, row in enumerate(stmt_rows):
        if level_max is not None and row.get("level", 99) > level_max:
            continue
        if normalize(row.get("name", "")) in keywords:
            return i
    return None


def _sum_child_values(child_rows, years_len):
    """child_rows: [(row, sign)] — sign 반영 합계(연도별). 값 없는 행은 제외."""
    totals = [0] * years_len
    any_value = False
    for row, sign in child_rows:
        values = row.get("values")
        if values is None:
            continue
        any_value = True
        for i in range(years_len):
            v = values[i] if i < len(values) else None
            if v is not None:
                totals[i] += sign * v
    return totals if any_value else None


def check_hierarchy_sums(stmt, years_len, report):
    """level1~3 헤더 행 = 바로 아래(직계) 자식 행들의 합(sign 반영).
    level0(총계)은 보통 항목들 뒤에 트레일링으로 오는 경우가 많아 제외하고,
    §6의 명명된 수식(check_balance_sheet_formulas/check_income_statement_formulas)에서 따로 다룬다."""
    title = stmt.get("title", "")
    rows = stmt.get("rows", [])

    stack = []  # (level, index)
    children = {}
    for i, row in enumerate(rows):
        level = row.get("level")
        if level is None:
            continue
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            children.setdefault(stack[-1][1], []).append(i)
        stack.append((level, i))

    for i, row in enumerate(rows):
        level = row.get("level")
        if level is None or level == 0 or level >= 4:
            continue
        kids = children.get(i, [])
        if not kids:
            continue
        parent_values = row.get("values")
        if parent_values is None:
            continue
        summed = _sum_child_values([(rows[k], rows[k].get("sign", 1)) for k in kids], years_len)
        if summed is None:
            continue
        for yi in range(years_len):
            pv = parent_values[yi] if yi < len(parent_values) else None
            if pv is None:
                continue
            if not _close(pv, summed[yi]):
                report.error(
                    f"[{title}] '{row.get('name')}' {yi + 1}번째 연도 값({pv:,.0f})이 "
                    f"하위 항목 합({summed[yi]:,.0f})과 일치하지 않습니다."
                )


_BS_KEYWORDS = {
    "자산총계": {"자산총계", "총자산"},
    "유동자산": {"유동자산"},
    "비유동자산": {"비유동자산", "고정자산"},
    "부채총계": {"부채총계", "총부채"},
    "유동부채": {"유동부채"},
    "비유동부채": {"비유동부채", "고정부채"},
    "자본총계": {"자본총계", "자본합계", "순자산"},
    "부채와자본총계": {"부채와자본총계", "부채및자본총계"},
}

_IS_KEYWORDS = {
    "매출액": {"매출액", "매출", "영업수익"},
    "매출원가": {"매출원가"},
    "매출총이익": {"매출총이익", "매출총손실"},
    "판매비와관리비": {"판매비와관리비", "판매관리비"},
    "영업이익": {"영업이익", "영업손실"},
    "영업외수익": {"영업외수익"},
    "영업외비용": {"영업외비용"},
    "법인세차감전순이익": {
        "법인세차감전순이익", "법인세비용차감전순이익", "법인세차감전계속사업이익", "법인세차감전손익",
    },
    "법인세비용": {"법인세비용", "법인세등"},
    "당기순이익": {"당기순이익", "당기순손실"},
}


def _val(rows, idx_map, key, yi):
    i = idx_map.get(key)
    if i is None:
        return None
    values = rows[i].get("values")
    if values is None or yi >= len(values):
        return None
    return values[yi]


def check_balance_sheet_formulas(stmt, years_len, report):
    rows = stmt.get("rows", [])
    idx = {k: _row_index(rows, kws) for k, kws in _BS_KEYWORDS.items()}

    for yi in range(years_len):
        asset_total = _val(rows, idx, "자산총계", yi)
        ca = _val(rows, idx, "유동자산", yi)
        nca = _val(rows, idx, "비유동자산", yi)
        if None not in (asset_total, ca, nca) and not _close(asset_total, ca + nca):
            report.error(
                f"[재무상태표] {yi + 1}번째 연도: 자산총계({asset_total:,.0f}) != "
                f"유동자산+비유동자산({ca + nca:,.0f})"
            )

        liab_total = _val(rows, idx, "부채총계", yi)
        cl = _val(rows, idx, "유동부채", yi)
        ncl = _val(rows, idx, "비유동부채", yi)
        if None not in (liab_total, cl, ncl) and not _close(liab_total, cl + ncl):
            report.error(
                f"[재무상태표] {yi + 1}번째 연도: 부채총계({liab_total:,.0f}) != "
                f"유동부채+비유동부채({cl + ncl:,.0f})"
            )

        equity_total = _val(rows, idx, "자본총계", yi)
        combined = _val(rows, idx, "부채와자본총계", yi)
        if combined is not None and asset_total is not None:
            if not _close(asset_total, combined):
                report.error(
                    f"[재무상태표] {yi + 1}번째 연도: 자산총계({asset_total:,.0f}) != "
                    f"부채와자본총계({combined:,.0f})"
                )
        elif None not in (asset_total, liab_total, equity_total):
            expect = liab_total + equity_total
            if not _close(asset_total, expect):
                report.error(
                    f"[재무상태표] {yi + 1}번째 연도: 자산총계({asset_total:,.0f}) != "
                    f"부채총계+자본총계({expect:,.0f})"
                )


def check_income_statement_formulas(stmt, years_len, report):
    rows = stmt.get("rows", [])
    idx = {k: _row_index(rows, kws) for k, kws in _IS_KEYWORDS.items()}

    for yi in range(years_len):
        rev = _val(rows, idx, "매출액", yi)
        cogs = _val(rows, idx, "매출원가", yi)
        gross = _val(rows, idx, "매출총이익", yi)
        if None not in (rev, cogs, gross) and not _close(gross, rev - cogs):
            report.error(
                f"[손익계산서] {yi + 1}번째 연도: 매출총이익({gross:,.0f}) != 매출액-매출원가({rev - cogs:,.0f})"
            )

        sga = _val(rows, idx, "판매비와관리비", yi)
        op = _val(rows, idx, "영업이익", yi)
        if None not in (gross, sga, op) and not _close(op, gross - sga):
            report.error(
                f"[손익계산서] {yi + 1}번째 연도: 영업이익({op:,.0f}) != 매출총이익-판관비({gross - sga:,.0f})"
            )

        non_op_rev = _val(rows, idx, "영업외수익", yi)
        non_op_exp = _val(rows, idx, "영업외비용", yi)
        pretax = _val(rows, idx, "법인세차감전순이익", yi)
        if None not in (op, non_op_rev, non_op_exp, pretax):
            expect = op + non_op_rev - non_op_exp
            if not _close(pretax, expect):
                report.error(
                    f"[손익계산서] {yi + 1}번째 연도: 법인세차감전순이익({pretax:,.0f}) != "
                    f"영업이익+영업외수익-영업외비용({expect:,.0f})"
                )

        tax = _val(rows, idx, "법인세비용", yi)
        net = _val(rows, idx, "당기순이익", yi)
        if None not in (pretax, tax, net) and not _close(net, pretax - tax):
            report.error(
                f"[손익계산서] {yi + 1}번째 연도: 당기순이익({net:,.0f}) != "
                f"법인세차감전순이익-법인세비용({pretax - tax:,.0f})"
            )


def check_cross_block(data, years_len, report):
    stmts = {s.get("title"): s for s in data.get("statements", [])}
    is_stmt = stmts.get("손익계산서")
    ap_stmt = stmts.get("이익잉여금처분계산서") or stmts.get("결손금처리계산서")

    if is_stmt and ap_stmt:
        is_idx = _row_index(is_stmt.get("rows", []), _IS_KEYWORDS["당기순이익"])
        ap_idx = _row_index(ap_stmt.get("rows", []), {"당기순이익", "당기순손실"})
        if is_idx is not None and ap_idx is not None:
            iv = is_stmt["rows"][is_idx].get("values") or []
            av = ap_stmt["rows"][ap_idx].get("values") or []
            for yi in range(min(len(iv), len(av), years_len)):
                if iv[yi] is not None and av[yi] is not None and not _close(iv[yi], av[yi]):
                    report.error(
                        f"[블록간] {yi + 1}번째 연도: 손익계산서 당기순이익({iv[yi]:,.0f}) != "
                        f"처분계산서 당기순이익({av[yi]:,.0f})"
                    )

    mc_stmt = stmts.get("제조원가명세서")
    if mc_stmt and is_stmt:
        mc_idx = _row_index(mc_stmt.get("rows", []), {"당기제품제조원가"})
        cogs_detail_idx = _row_index(is_stmt.get("rows", []), {"당기제품제조원가"})
        if mc_idx is not None and cogs_detail_idx is not None:
            mv = mc_stmt["rows"][mc_idx].get("values") or []
            cv = is_stmt["rows"][cogs_detail_idx].get("values") or []
            for yi in range(min(len(mv), len(cv), years_len)):
                if mv[yi] is not None and cv[yi] is not None and not _close(mv[yi], cv[yi]):
                    report.error(
                        f"[블록간] {yi + 1}번째 연도: 제조원가명세서 당기제품제조원가({mv[yi]:,.0f}) != "
                        f"손익계산서 내 당기제품제조원가({cv[yi]:,.0f})"
                    )


def check_warnings(data, years_len, report):
    for stmt in data.get("statements", []):
        title = stmt.get("title", "")
        for row in stmt.get("rows", []):
            name = row.get("name", "")
            if row.get("note"):
                report.warn(f"[{title}] '{name}': {row['note']}")
                continue
            values = row.get("values")
            if values is None:
                continue
            if any(v is None for v in values):
                report.warn(f"[{title}] '{name}': 일부 연도 값이 null 입니다 — 확인이 필요합니다.")
            elif values and all((v or 0) == 0 for v in values):
                report.warn(f"[{title}] '{name}': 모든 연도 값이 0입니다 — 원본에 실제로 0인지 확인하세요.")

    stmts = {s.get("title"): s for s in data.get("statements", [])}
    ap_stmt = stmts.get("이익잉여금처분계산서") or stmts.get("결손금처리계산서")
    if ap_stmt:
        rows = ap_stmt.get("rows", [])
        begin_idx = _row_index(rows, {"기초이익잉여금", "전기이월이익잉여금", "미처분이익잉여금기초"})
        end_idx = _row_index(rows, {"기말이익잉여금", "차기이월이익잉여금", "미처분이익잉여금기말"})
        if begin_idx is not None and end_idx is not None:
            bv = rows[begin_idx].get("values") or []
            ev = rows[end_idx].get("values") or []
            for yi in range(1, min(len(bv), len(ev), years_len)):
                if bv[yi] is not None and ev[yi - 1] is not None and not _close(bv[yi], ev[yi - 1]):
                    report.warn(
                        f"[{ap_stmt.get('title')}] {yi + 1}번째 연도 기초이익잉여금({bv[yi]:,.0f})이 "
                        f"전기 기말이익잉여금({ev[yi - 1]:,.0f})과 다릅니다 — 적립금 이동 등으로 정상일 수 있습니다."
                    )


def run(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    report = Report()
    years = data.get("years") or []
    years_len = len(years)

    check_structure(data, report)
    if years_len:
        for stmt in data.get("statements", []):
            check_hierarchy_sums(stmt, years_len, report)
            if stmt.get("title") == "재무상태표":
                check_balance_sheet_formulas(stmt, years_len, report)
            elif stmt.get("title") == "손익계산서":
                check_income_statement_formulas(stmt, years_len, report)
        check_cross_block(data, years_len, report)
        check_warnings(data, years_len, report)

    print(f"=== RAW 입력 검증: {path} ===")
    print(f"연도 수: {years_len} / 블록 수: {len(data.get('statements', []))}\n")

    if report.errors:
        print(f"[ERROR] {len(report.errors)}건 — 반드시 수정하거나, 원본 자체의 불일치면 보고서에 명시하세요 (§1-5)")
        for e in report.errors:
            print(f"  x {e}")
    else:
        print("[ERROR] 없음")

    print()
    if report.warns:
        print(f"[WARN] {len(report.warns)}건 — 하나씩 확인하세요")
        for w in report.warns:
            print(f"  ! {w}")
    else:
        print("[WARN] 없음")

    print(
        "\n[참고] 원본에 있는데 JSON에 아예 없는 계정은 이 스크립트가 찾아내지 못합니다.\n"
        "       절차 2의 '원본 계정 수 = JSON 행 수' 대조를 사람이 직접 확인하세요 (§6)."
    )

    return 1 if report.errors else 0


def main():
    if len(sys.argv) != 2:
        print("사용법: python scripts/check_raw.py <raw_input.json>")
        sys.exit(2)
    sys.exit(run(sys.argv[1]))


if __name__ == "__main__":
    main()
