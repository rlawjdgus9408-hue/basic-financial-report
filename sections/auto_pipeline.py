"""
고객사 전용 자동분석 파이프라인.

내부 제작용 앱은 "자료 업로드 -> 재무 데이터 검토 -> 종합의견 작성"을 사람이 단계마다
확인하며 진행하지만, 고객용은 자료를 넣으면 그 뒤로 사람 개입 없이:
  1. 재무지표 계산 (sections.metrics.compute_all_metrics)
  2. 문서에 넣을 지표를 자동 선택 (기초재무진단 스킬 Q4-1 표준 지표 + Q4-3 병기 지표)
  3. 스킬 Q4-4 기준 그래프 2~3개를 이미지로 생성 (보고서 삽입용)
  4. AI가 핵심 계정·지표 코멘트 작성 (스킬 Q2·Q3)
  5. AI가 종합의견(Executive Summary) 작성 — 4의 결과(보고서 지면)를 근거로 (executive-summary 스킬)
을 한 번에 수행한다. 계산 로직 자체는 인터랙티브 화면(metrics.py, comment.py)과 100%
공유하므로, 두 화면이 서로 다른 답을 내는 일이 없다.
"""
import streamlit as st

from sections.metrics import (
    compute_all_metrics,
    BS_INDICATORS,
    IS_INDICATORS,
    COMMON_INDICATORS,
    _get_metric_val,
    _find_account_values,
    _pick_won_scale,
    _build_combo_chart_png,
    _build_line_chart_png,
)
from sections.comment import (
    build_indicator_table,
    _system_instruction,
    _plain_text_ai_answer,
    _quick_style_check,
)
from sections.diagnosis import DIAGNOSIS_QUESTIONS
from sections.ai_client import configured_value, ai_model, generate_text
from sections.account_comments import generate_account_comments

_ALL_INDICATOR_ORDER = BS_INDICATORS + IS_INDICATORS + COMMON_INDICATORS

# 기초재무진단 스킬 Q4-1 표준 지표(재무상태표 기반 5개 / 손익계산서 기반 5개)에 Q4-3 병기
# 규칙(유동비율 → 당좌비율, 영업이익 지표 → 판관비율)을 더한 고정 목록. 스킬 표기 → 앱 지표명:
# 매출성장률 → 매출액증가율, 이자보상배수 → 이자보상배율. 차입금의존도와 이자보상배율은
# Q4-3에 따라 항상 함께 들어간다.
AUTO_INDICATORS = [
    '총자산증가율', '부채비율', '차입금의존도', '유동비율', '당좌비율', '현금전환주기',
    '매출액증가율', '매출총이익률', '영업이익률', '판매관리비율', 'ROA', '이자보상배율',
]

# 종합의견 분량(자). ES 스킬 기본값은 700~1,100자지만, 스킬 §1의 "사용자가 분량을 지정하면 그 값을
# 상한으로 보고 −10%까지 허용" 규칙으로 1,500자를 지정한다(1,350~1,500자).
# scripts/check_es.py의 CHAR_*_WARN 기준과 함께 맞춘다.
ES_TARGET_CHARS = 1500

# 파이프라인이 채우는 결과 키 — 매 실행 시작 시 전부 비운다. 중간 단계가 실패해 return해도
# 이전 업로드(다른 회사일 수 있음)의 결과가 다음 보고서에 섞여 들어가지 않게 하기 위함.
_RESULT_DEFAULTS = {
    'bs_metrics': {}, 'is_metrics': {}, 'common_metrics': {},
    'selected_indicators_table': '',
    'selected_indicators_data': [],
    'selected_indicators_bs_data': [],
    'selected_indicators_is_data': [],
    'auto_chart_specs': [],
    'account_bs_comments': [], 'account_is_comments': [],
    'indicator_bs_comments': [], 'indicator_is_comments': [],
    'auto_account_comment_warnings': [],
    'auto_es_warnings': [],
    'txt_exec': '', 'exec_summary': '',
}


def _split_selected_indicators(indicator_names):
    """지표명 목록을 report.py/comment.py가 기대하는 {'bs':[...], 'is':[...], 'common':[...]}
    구조로 나눈다(원래 출처 분류 기준)."""
    names = set(indicator_names)
    return {
        'bs': [i for i in BS_INDICATORS if i in names],
        'is': [i for i in IS_INDICATORS if i in names],
        'common': [i for i in COMMON_INDICATORS if i in names],
    }


def _ratio_series(indicator, years, bs_metrics, is_metrics, common_metrics):
    return [_get_metric_val(indicator, yr, bs_metrics, is_metrics, common_metrics) for yr in years]


def build_chart_specs(bs_metrics, is_metrics, common_metrics, years, df_bs):
    """anthropic-skills:기초재무진단 스킬의 Q4-4(그래프 추천) 규칙을 그대로 따른다 — 백화점식
    나열 대신 '채택 기본값: 수익성 시소 + 자본 구조' 2개를 고정으로 쓰고, 재고·매출채권
    변동이 뚜렷할 때만 '현금·유동성' 콤보를 3번째로 추가한다. 차트 제목·범례는 바로 옆에
    붙는 원본 데이터 표(report.py가 렌더링)의 글자와 정확히 같아야 하므로, 반환하는 각
    spec에 'table_rows'로 그 원본 표 데이터를 함께 담아 report.py가 재계산 없이 그대로
    옆 표에 쓸 수 있게 한다.

    값이 없는 연도는 0으로 채우지 않고 None 그대로 넘긴다 — plotly가 그 구간을 비워 그려,
    옆 표의 '-'와 차트가 같은 사실을 보여준다.

    반환: ([{'title', 'png_bytes', 'table_header', 'table_rows'}, ...], [오류 메시지, ...]).
    실패한 차트는 목록에서 빠지고 사유만 남긴다 — 보고서 생성 자체를 막지 않기 위함."""
    specs, errors = [], []

    # 1) 수익성 지표 (고정) — 매출원가율·판매관리비율·영업이익률 3선
    try:
        names = ['매출원가율', '판매관리비율', '영업이익률']
        series = [(n, _ratio_series(n, years, bs_metrics, is_metrics, common_metrics)) for n in names]
        series = [(n, v) for n, v in series if any(x is not None for x in v)]
        if series:
            png = _build_line_chart_png('수익성 지표', series, years)
            specs.append({
                'title': '수익성 지표',
                'png_bytes': png,
                'table_header': ['지표명'] + list(years),
                'table_rows': [[n] + [f"{x:.1f}%" if x is not None else '-' for x in v] for n, v in series],
            })
    except Exception as error:
        errors.append(f"수익성 지표 그래프: {error}")

    # 2) 자본 구조 (고정) — 부채총계·자본총계(원본 금액, 막대) + 부채비율(선, 보조축)
    try:
        liabilities = _find_account_values(df_bs, '부채총계', years)
        equity = _find_account_values(df_bs, '자본총계', years)
        debt_ratio = _ratio_series('부채비율', years, bs_metrics, is_metrics, common_metrics)
        if liabilities and equity and any(x is not None for x in debt_ratio):
            divisor, unit = _pick_won_scale(liabilities + equity)
            bar_series = [('부채총계', [v / divisor for v in liabilities]), ('자본총계', [v / divisor for v in equity])]
            png = _build_combo_chart_png('자본 구조', bar_series, [('부채비율', debt_ratio)], years)
            specs.append({
                'title': '자본 구조',
                'png_bytes': png,
                'table_header': ['구분'] + list(years),
                'table_rows': [
                    ['부채총계'] + [f"{v / divisor:.1f}{unit}" for v in liabilities],
                    ['자본총계'] + [f"{v / divisor:.1f}{unit}" for v in equity],
                    ['부채비율'] + [f"{x:.1f}%" if x is not None else '-' for x in debt_ratio],
                ],
            })
    except Exception as error:
        errors.append(f"자본 구조 그래프: {error}")

    # 3) 현금·유동성 (조건부) — 재고자산+매출채권 합계가 첫해 대비 마지막해 30% 이상
    # 변동할 때만 추가한다(사람이 ES 메시지를 보고 고르는 과정을 자동화에선 데이터 기반
    # 규칙으로 대체 — 재고/매출채권 변동이 크다는 건 단기 현금흐름 이슈가 있다는 신호).
    try:
        inventory = _find_account_values(df_bs, '재고자산', years)
        receivable = _find_account_values(df_bs, '매출채권', years)
        cash = _find_account_values(df_bs, '현금', years)
        current_ratio = _ratio_series('유동비율', years, bs_metrics, is_metrics, common_metrics)
        significant = False
        if inventory and receivable:
            combined = [i + r for i, r in zip(inventory, receivable)]
            if combined[0]:
                significant = abs((combined[-1] - combined[0]) / combined[0]) >= 0.3
        if significant and cash and any(x is not None for x in current_ratio):
            divisor, unit = _pick_won_scale(cash)
            png = _build_combo_chart_png(
                '현금·유동성', [('현금성자산', [v / divisor for v in cash])],
                [('유동비율', current_ratio)], years,
            )
            specs.append({
                'title': '현금·유동성',
                'png_bytes': png,
                'table_header': ['구분'] + list(years),
                'table_rows': [
                    ['현금성자산'] + [f"{v / divisor:.1f}{unit}" for v in cash],
                    ['유동비율'] + [f"{x:.1f}%" if x is not None else '-' for x in current_ratio],
                ],
            })
    except Exception as error:
        errors.append(f"현금·유동성 그래프: {error}")

    return [s for s in specs if s.get('png_bytes')], errors


def _company_context(company_info):
    """스킬의 정체성·산업 특성 판단(executive-summary §2-1, 기초재무진단 Q0-2 ①)에 쓰는 기업 정보."""
    info = company_info or {}
    erp = info.get('erp_system', '')
    if isinstance(erp, list):
        erp = ', '.join(erp)
    rows = [
        ("기업명", info.get('company_name', '')),
        ("업종", info.get('biz_type', '')),
        ("개업일", info.get('biz_start_date', '')),
        ("종업원 수", info.get('emp_count', '')),
        ("사용 중인 회계·ERP 시스템", erp),
        ("특이사항(고객 기재)", info.get('special_note', '')),
    ]
    return "\n".join(f"- {k}: {v}" for k, v in rows if v)


def _diagnosis_context(diagnosis):
    """사전 검토사항 응답과 관리 방향성 — executive-summary §0-3·§0-8·§3-4가 요구하는 입력."""
    if not diagnosis:
        return "(제공되지 않음)"
    answers = diagnosis.get('check_results') or []
    lines = [f"{i + 1}. {q} → {answers[i] if i < len(answers) and answers[i] else '미응답'}"
             for i, q in enumerate(DIAGNOSIS_QUESTIONS)]
    no_count = sum(1 for a in answers if a == '아니오')
    lines.append(f"'아니오'(개선 필요) 응답 수: {no_count}개 / {len(DIAGNOSIS_QUESTIONS)}개")
    dirs = list(diagnosis.get('selected_dirs') or [])
    if diagnosis.get('dir_etc'):
        dirs.append(diagnosis['dir_etc'])
    lines.append(f"재무관리 방향성(고객 선택): {', '.join(dirs) if dirs else '(선택 없음)'}")
    return "\n".join(lines)


def _report_page_context(df_bs, df_is, years):
    """보고서에 실제로 인쇄되는 재무분석 표(핵심 계정 + 지표 + 각 코멘트)와 그래프 옆 원천 표.
    executive-summary §0-7(근거 범위 = 보고서 지면)에 따라 ES는 이 범위 안의 수치만 쓴다."""
    from sections.report import _account_row  # report.py와 같은 방식으로 원본 금액을 찾는다

    color_names = {'sky': '하늘색', 'gray': '회색', 'orange': '주황'}
    year_cols = "\t".join(years)

    def _comment_cols(item):
        return f"Level {item.get('level', '-')}\t{color_names.get(item.get('color'), '-')}\t{item.get('comment', '')}"

    sections = []
    for title, items, df in (
        ("재무상태표 (단위: 원)", st.session_state.get('account_bs_comments'), df_bs),
        ("손익계산서 (단위: 원)", st.session_state.get('account_is_comments'), df_is),
    ):
        if not items:
            continue
        lines = [f"[{title}]", f"계정과목\t{year_cols}\tLevel\t색상\t코멘트"]
        for item in items:
            row = _account_row(item, df, years)
            lines.append("\t".join(str(v) for v in row[:-1]) + "\t" + _comment_cols(item))
        sections.append("\n".join(lines))

    for title, items, rows in (
        ("재무상태표 관련 지표", st.session_state.get('indicator_bs_comments'),
         st.session_state.get('selected_indicators_bs_data')),
        ("손익계산서 관련 지표", st.session_state.get('indicator_is_comments'),
         st.session_state.get('selected_indicators_is_data')),
    ):
        if not rows:
            continue
        comments = {i.get('account'): i for i in (items or [])}
        lines = [f"[{title}] (비율·증가율 %, 기간 일, 이자보상배율 배)", f"지표명\t{year_cols}\tLevel\t색상\t코멘트"]
        for r in rows:
            item = comments.get(r['지표명'], {})
            lines.append(r['지표명'] + "".join(f"\t{r.get(y, '-')}" for y in years) + "\t" + _comment_cols(item))
        sections.append("\n".join(lines))

    for spec in st.session_state.get('auto_chart_specs') or []:
        lines = [f"[그래프: {spec['title']}]", "\t".join(spec['table_header'])]
        lines += ["\t".join(str(v) for v in row) for row in spec['table_rows']]
        sections.append("\n".join(lines))

    return "\n\n".join(sections) if sections else "(보고서 재무분석 표를 만들지 못했습니다)"


def generate_exec_summary(api_key, model, df_bs, df_is, years, company_info=None, diagnosis=None):
    """보고서 지면(계정·지표 코멘트 표, 그래프 원천 표)과 기업 정보·사전 검토사항을 근거로
    AI가 종합의견을 한 번에 작성하게 한다. 시스템 지시는 comment.py와 같은 ES 스킬 원문에
    자동 실행 안내를 붙인 것이고, 후처리(마크다운 정리 + 자동 검수)도 그대로 재사용한다.
    사람이 다시 눌러줄 버튼이 없는 완전 자동 흐름이라 AI 서버 일시 과부하(529 등)에는 재시도한다."""
    import time as _time

    from sections.convert import _is_transient_error, _MAX_RETRIES

    prompt = f"""아래 자료를 근거로 기초재무진단보고서 1페이지 종합의견(Executive Summary)을 작성하세요.

[기업 정보]
{_company_context(company_info) or "(제공되지 않음)"}

[사전 검토사항 응답]
{_diagnosis_context(diagnosis)}

[보고서 재무분석 표 — 계정·지표 코멘트는 이미 확정됨]
연도는 왼쪽이 오래된 연도, 오른쪽이 최신 연도입니다.
{_report_page_context(df_bs, df_is, years)}

[출력 형식]
- 분량: {ES_TARGET_CHARS:,}자 (사용자 지정 분량 — 규칙 §1에 따라 상한으로 보고 {int(ES_TARGET_CHARS * 0.9):,}~{ES_TARGET_CHARS:,}자로 씁니다).
- 종합의견 본문만 출력합니다. '종합의견(Executive Summary)' 같은 제목, 구분선(---), 작성 메모나 확인 요청 문단은 넣지 않습니다.
- 단락은 빈 줄로 구분합니다. 마크다운 기호(**, #)는 쓰지 않습니다.
"""
    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            raw = generate_text(api_key, model, _system_instruction(auto=True), prompt)
            cleaned = _plain_text_ai_answer(raw)
            warnings = _quick_style_check(cleaned)
            return cleaned, warnings
        except Exception as error:
            last_error = error
            if not _is_transient_error(error) or attempt == _MAX_RETRIES - 1:
                raise
            _time.sleep(3 * (attempt + 1))
    raise last_error


def pipeline_key(years, df_bs, df_is):
    """같은 업로드 결과에 대해 파이프라인을 중복 실행(=AI 재호출)하지 않기 위한 식별 키.

    연도/행 개수 같은 '모양'만 비교하면, 내용이 다른데 모양만 같은 재업로드(예: 숫자를 고쳐
    같은 연도 수·같은 행 수로 재업로드)에 이전 분석 결과(지표·그래프·AI 종합의견)를 그대로
    재사용해버리는 사고가 날 수 있다 — 실제 셀 값까지 해시에 반영한다."""
    import hashlib

    payload = f"{list(years)}|{df_bs.to_csv()}|{df_is.to_csv()}".encode("utf-8")
    return hashlib.md5(payload).hexdigest()


def run_auto_analysis(df_bs, df_is, years, company_info=None, diagnosis=None, on_progress=None):
    """업로드된 BS/IS로 지표 계산 -> 지표 선택 -> 그래프 생성 -> 계정·지표 코멘트 ->
    종합의견 생성까지 한 번에 수행하고, 최종보고서 생성에 필요한 값들을 session_state에 채운다.

    company_info(render_company_info 결과)와 diagnosis({'check_results','selected_dirs','dir_etc'})는
    스킬이 요구하는 정체성·산업·사전 검토사항 판단에 쓰도록 AI 프롬프트에 넘긴다.

    AI 호출이 실패해도(키 미설정, 네트워크 오류 등) 예외를 밖으로 던지지 않는다 — 해당 결과만
    비운 채로 두고 사유를 session_state['auto_pipeline_error']에 남겨, 나머지(지표·그래프)는
    그대로 보고서에 쓸 수 있게 한다. 고객용 흐름은 내부용과 달리 업로드와 보고서 생성 사이에
    사람이 추출 결과를 검토하는 화면이 없으므로, 지표 계산 자체(AI 추출 결과가 예상과 다른
    모양일 때 등)가 실패해도 여기서 막아 화면이 통째로 깨지지 않게 한다.

    on_progress(pct, message)가 주어지면 단계가 바뀔 때마다 호출해 호출부(main.py)가
    진행률 표시줄을 갱신할 수 있게 한다 — 생략하면(None) 조용히 넘어간다."""
    def _progress(pct, message):
        if on_progress is not None:
            on_progress(pct, message)

    def _add_error(message):
        st.session_state['auto_pipeline_error'] = (
            st.session_state.get('auto_pipeline_error', '') + " " + message
        ).strip()

    st.session_state.pop('auto_pipeline_error', None)
    for key, default in _RESULT_DEFAULTS.items():
        st.session_state[key] = type(default)()
    st.session_state['years'] = years

    _progress(5, "재무지표를 계산하는 중입니다...")
    try:
        bs_metrics, is_metrics, common_metrics = compute_all_metrics(df_bs, df_is, years)
        st.session_state['bs_metrics'] = bs_metrics
        st.session_state['is_metrics'] = is_metrics
        st.session_state['common_metrics'] = common_metrics

        all_selected = sorted(AUTO_INDICATORS, key=_ALL_INDICATOR_ORDER.index)
        st.session_state['selected_indicators'] = _split_selected_indicators(all_selected)

        table_data, table_text = build_indicator_table(
            all_selected, years, bs_metrics, is_metrics, common_metrics, drop_empty=True
        )
        st.session_state['selected_indicators_table'] = table_text
        st.session_state['selected_indicators_data'] = table_data
        # 재무분석 섹션에서 재무상태표/손익계산서 표 바로 밑에 각자 관련 지표만 보여주기 위해
        # 미리 나눠둔다(공통 지표 ROA·이자보상배율은 스킬 Q4-1에서 손익계산서 기반이다).
        st.session_state['selected_indicators_bs_data'] = [r for r in table_data if r['지표명'] in BS_INDICATORS]
        st.session_state['selected_indicators_is_data'] = [
            r for r in table_data if r['지표명'] in IS_INDICATORS or r['지표명'] in COMMON_INDICATORS
        ]
    except Exception as error:
        _add_error(f"재무지표 계산 중 오류: {error}")
        _progress(100, "오류로 중단됨")
        return

    _progress(35, "그래프를 생성하는 중입니다...")
    try:
        specs, chart_errors = build_chart_specs(bs_metrics, is_metrics, common_metrics, years, df_bs)
        st.session_state['auto_chart_specs'] = specs
        if chart_errors:
            _add_error("그래프 생성 중 오류: " + "; ".join(chart_errors))
    except Exception as error:
        _add_error(f"그래프 생성 중 오류: {error}")

    api_key = configured_value("Claude", "api_key")
    model = ai_model()
    if not api_key:
        _add_error("Claude API 키가 설정되지 않아 계정별 코멘트·종합의견을 자동 생성하지 못했습니다.")
        _progress(100, "오류로 중단됨")
        return

    _progress(45, "계정별 코멘트를 작성하는 중입니다...")
    try:
        result = generate_account_comments(
            api_key, model, df_bs, df_is, years,
            bs_indicator_rows=st.session_state.get('selected_indicators_bs_data'),
            is_indicator_rows=st.session_state.get('selected_indicators_is_data'),
            company_context=_company_context(company_info),
        )
        st.session_state['account_bs_comments'] = result['bs_accounts']
        st.session_state['account_is_comments'] = result['is_accounts']
        st.session_state['indicator_bs_comments'] = result['bs_indicators']
        st.session_state['indicator_is_comments'] = result['is_indicators']
        st.session_state['auto_account_comment_warnings'] = result['warnings']
    except Exception as error:
        _add_error(f"계정별 코멘트 생성 중 오류: {error}")

    _progress(70, "AI가 종합의견(서머리)을 작성하는 중입니다...")
    try:
        exec_summary, warnings = generate_exec_summary(
            api_key, model, df_bs, df_is, years, company_info=company_info, diagnosis=diagnosis,
        )
        st.session_state['txt_exec'] = exec_summary
        st.session_state['exec_summary'] = exec_summary
        st.session_state['auto_es_warnings'] = warnings
    except Exception as error:
        _add_error(f"AI 종합의견 생성 중 오류: {error}")

    _progress(100, "분석 완료")
