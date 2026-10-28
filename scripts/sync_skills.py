"""
Claude Code 스킬 원문을 앱의 skills/ 폴더로 옮겨 넣는다.

앱(sections/ai_client.py)은 skills/ 아래 기초재무진단·executive-summary 원문을 AI 시스템 지시문으로
그대로 읽는다. 스킬을 고친 뒤 이 스크립트로 한 번 복사하면 코드 수정 없이 반영된다.

사용법:
    python scripts/sync_skills.py <스킬 zip 파일 또는 스킬 폴더들이 들어있는 폴더>

예:
    python scripts/sync_skills.py claude-code-skills.zip
    python scripts/sync_skills.py "%USERPROFILE%/.claude/skills/synced/<id>"
"""
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SKILL_NAMES = ["기초재무진단", "executive-summary"]
DEST = Path(__file__).parent.parent / "skills"


def _extract_zip(zip_path, out_dir):
    """Windows 탐색기로 만든 zip은 한글 파일명에 UTF-8 플래그가 없어 cp437로 잘못 읽힌다 —
    플래그가 없으면 cp437 바이트를 UTF-8로 다시 해석한다."""
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            name = info.filename
            if not info.flag_bits & 0x800:
                try:
                    name = name.encode("cp437").decode("utf-8")
                except UnicodeDecodeError:
                    pass
            target = (out_dir / name).resolve()
            if out_dir.resolve() not in target.parents and target != out_dir.resolve():
                raise ValueError(f"zip 안에 폴더 밖을 가리키는 경로가 있습니다: {name}")
            if name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    source = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as tmp:
        if source.suffix.lower() == ".zip":
            root = Path(tmp)
            _extract_zip(source, root)
        else:
            root = source

        missing = [n for n in SKILL_NAMES if not (root / n / "SKILL.md").is_file()]
        if missing:
            print(f"오류: {root} 에서 다음 스킬의 SKILL.md를 찾지 못했습니다: {', '.join(missing)}")
            return 1

        for name in SKILL_NAMES:
            dest = DEST / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(root / name, dest, ignore=shutil.ignore_patterns(".w", "__pycache__"))
            count = sum(1 for p in dest.rglob("*") if p.is_file())
            print(f"{name}: 파일 {count}개 복사 → {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
