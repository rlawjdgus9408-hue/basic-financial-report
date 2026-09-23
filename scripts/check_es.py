"""
Executive Summary(종합의견) 자동 검수 스크립트.

docs/es_guideline.md 의 작성 규칙 중 프로그램적으로 확인 가능한 항목만 검사한다.
§7 "수동 체크리스트" 항목(첫 문장이 회사 정체성으로 시작하는지, 인과 단정이 근거에 맞는지 등)은
사람의 판단이 필요해 이 스크립트가 검사하지 않는다 — 실행 후 안내되는 체크리스트를 직접 확인할 것.

사용법:
    python scripts/check_es.py <es_draft.txt>

종료 코드: ERROR가 하나라도 있으면 1, 없으면 0 (WARN만 있어도 0).
"""
import re
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서도 한글/특수문자(—, § 등)가 깨지지 않도록 UTF-8로 강제한다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# §4-4 금지 표현
BANNED_PHRASES = [
    "착시", "도산", "부재", "폭발적", "사상 최대", "잠식", "이대로 가면",
    "시사합니다", "가능성이 있습니다", "하세요", "이익의 질", "매출 mix", "매출 주도형 성장",
]

# §4-3 영어 약어 금지
ENGLISH_ABBR = {
    "GPM": "매출총이익률", "OPM": "영업이익률", "NPM": "순이익률",
    "DSO": "매출채권 회수기간", "DIO": "재고자산 회전일수",
    "DPO": "매입채무 결제기간", "CCC": "현금전환주기",
}

# §4-5 종결 표현
ENDING_PATTERNS = ["진단됩니다", "판단됩니다", "평가됩니다", "확인됩니다", "보입니다", "필요합니다"]
HEDGE_PATTERNS = ["시점으로 보입니다", "것으로 보입니다", "시점으로 판단됩니다"]

# §1 분량 — 700~900자 권장(WARN), 500~1200자 밖이면 ERROR
CHAR_MIN_WARN, CHAR_MAX_WARN = 700, 900
CHAR_MIN_ERROR, CHAR_MAX_ERROR = 500, 1200
MAX_SENTENCES_PER_PARAGRAPH = 5

MAX_ARROWS = 2  # §4-2
MAX_UNHEDGED_PILYO = 1  # §4-5
MIN_ENDING_VARIETY = 4  # §4-5

SERVICE_NAMES = ["그로스파이낸스", "구독형 재무팀", "CFO 서비스"]  # §2-3


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def _char_count(text):
    """공백을 제외한 글자수 (한글 원고 분량 기준)."""
    return len(re.sub(r"\s", "", text))


def _split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def _split_sentences(paragraph):
    """대략적인 문장 분리 (완벽하지 않음 — 참고용 WARN 판단에만 사용)."""
    sentences = re.split(r"(?<=[다요]\.)\s+|(?<=[.!?])\s+", paragraph.strip())
    return [s for s in sentences if s.strip()]


def check_length(text, report):
    n = _char_count(text)
    if n < CHAR_MIN_ERROR or n > CHAR_MAX_ERROR:
        report.error(f"글자수 {n}자 — 허용 범위({CHAR_MIN_ERROR}~{CHAR_MAX_ERROR}자)를 벗어났습니다.")
    elif n < CHAR_MIN_WARN or n > CHAR_MAX_WARN:
        report.warn(f"글자수 {n}자 — 권장 범위({CHAR_MIN_WARN}~{CHAR_MAX_WARN}자) 밖입니다 (§1).")


def check_paragraphs(text, report):
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) not in (3, 4):
        report.warn(f"단락 수 {len(paragraphs)}개 — 기본 3단락(예외적으로 4단락)을 벗어났습니다 (§1).")
    for i, p in enumerate(paragraphs, start=1):
        sentences = _split_sentences(p)
        if len(sentences) > MAX_SENTENCES_PER_PARAGRAPH:
            report.warn(f"{i}단락 문장 수 {len(sentences)}개 — 4~5문장 이내 권장을 초과했습니다 (§1).")
    return paragraphs


def check_banned_phrases(text, report):
    for phrase in BANNED_PHRASES:
        if phrase in text:
            report.error(f"금지 표현 발견: '{phrase}' (§4-4)")


def check_abbreviations(text, report):
    # \b는 한글 뒤에서 단어 경계로 인식되지 않아 "GPM이"처럼 조사가 바로 붙는 경우를 놓친다.
    # 앞뒤로 영문/숫자만 아니면(한글 조사가 바로 붙어도) 매치되도록 lookaround로 대체한다.
    for abbr, ko in ENGLISH_ABBR.items():
        if re.search(rf"(?<![A-Za-z0-9]){abbr}(?![A-Za-z0-9])", text):
            report.error(f"영어 약어 '{abbr}' 사용 — '{ko}'로 풀어써야 합니다 (§4-3).")


def check_million_won(text, report):
    if "백만원" in text:
        report.error("'백만원' 단위 표기 발견 — 억/천만 단위로 환산해야 합니다 (§4-1).")


def check_arrows(text, report):
    count = text.count("→") + len(re.findall(r"\d\s*->\s*\d", text))
    if count > MAX_ARROWS:
        report.error(f"화살표(X%→Y%) 표기 {count}개 — 최대 {MAX_ARROWS}개까지만 허용됩니다 (§4-2).")


def check_ending_variety(paragraphs, report):
    used = set()
    unhedged_pilyo = 0
    for p in paragraphs:
        for pattern in ENDING_PATTERNS:
            if pattern in p:
                used.add(pattern)
        stripped = p.strip()
        if stripped.endswith("필요합니다.") or stripped.endswith("필요합니다"):
            if not any(stripped.endswith(h) or stripped.endswith(h + ".") for h in HEDGE_PATTERNS):
                unhedged_pilyo += 1
    if len(used) < MIN_ENDING_VARIETY:
        report.warn(
            f"종결 표현 다양성 부족 — {len(used)}종만 사용({', '.join(sorted(used)) or '없음'}). "
            f"{MIN_ENDING_VARIETY}종 이상 권장 (§4-5)."
        )
    if unhedged_pilyo > MAX_UNHEDGED_PILYO:
        report.warn(
            f"헤지 없는 '~필요합니다' 단정 마무리가 {unhedged_pilyo}문장 — "
            f"최대 {MAX_UNHEDGED_PILYO}개까지만 허용됩니다 (§4-5)."
        )


def check_numbered_bullets(text, report):
    if re.search(r"[①②③④⑤]", text):
        report.warn("①②③ 번호 기호 발견 — 보완사항은 번호 없이 자연어로 이어써야 합니다 (§2-3).")


def check_service_names(text, report):
    for name in SERVICE_NAMES:
        if name in text:
            report.warn(f"서비스·구독 상품명 '{name}' 발견 — 방향만 암시하고 상품명은 쓰지 않아야 합니다 (§2-3).")


def run(path):
    text = Path(path).read_text(encoding="utf-8")
    report = Report()

    check_length(text, report)
    paragraphs = check_paragraphs(text, report)
    check_banned_phrases(text, report)
    check_abbreviations(text, report)
    check_million_won(text, report)
    check_arrows(text, report)
    check_ending_variety(paragraphs, report)
    check_numbered_bullets(text, report)
    check_service_names(text, report)

    print(f"=== ES 자동 검수: {path} ===")
    print(f"글자수(공백 제외): {_char_count(text)}자 / 단락 수: {len(paragraphs)}개\n")

    if report.errors:
        print(f"[ERROR] {len(report.errors)}건 — 반드시 수정하세요")
        for e in report.errors:
            print(f"  x {e}")
    else:
        print("[ERROR] 없음")

    print()
    if report.warns:
        print(f"[WARN] {len(report.warns)}건 — 하나씩 판단해서 고치거나 유지 사유를 남기세요")
        for w in report.warns:
            print(f"  ! {w}")
    else:
        print("[WARN] 없음")

    print(
        "\n[다음 단계] docs/es_guideline.md의 '7. 수동 체크리스트'는 스크립트가 판단할 수 없습니다.\n"
        "           (첫 문장이 회사 정체성으로 시작하는지, 적자 원인이 증감 기여도 1위 항목과 일치하는지 등)\n"
        "           직접 확인하세요."
    )

    return 1 if report.errors else 0


def main():
    if len(sys.argv) != 2:
        print("사용법: python scripts/check_es.py <es_draft.txt>")
        sys.exit(2)
    sys.exit(run(sys.argv[1]))


if __name__ == "__main__":
    main()
