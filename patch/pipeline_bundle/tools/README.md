# Unified Translation Pipeline

저장소 루트에서 아래 명령으로 원본(ScummVM) + 인핸스드(리마스터) 파이프라인을 함께 실행할 수 있습니다.

```powershell
cd C:\Projects\BladeRunner-Kor
python tools\pipeline.py build-all
```

## Commands

```powershell
# 원본 입력 무결성 검증(ingame Filename/ID 기준)
python tools\pipeline.py validate

# 원본(ScummVM)만 빌드
python tools\pipeline.py build-classic --profile both
python tools\pipeline.py build-classic --profile windows_full
python tools\pipeline.py build-classic --profile subs_only

# 인핸스드(리마스터)만 빌드
python tools\pipeline.py build-enhanced

# 마스터 TSV에서 분해 + 연속 빌드
python tools\pipeline.py build-from-master

# 로컬 원문 추출만
python tools\pipeline.py extract-local --classic-game-dir "C:\Games\BladeRunner\Classic"

# 로컬 원문 추출 + 빌드
python tools\pipeline.py build-from-local --classic-game-dir "C:\Games\BladeRunner\Classic" --target classic
```

## Translation Workflow (TSV Master)

단일 번역 TSV 기반 워크플로우는 아래 문서를 따릅니다.

- `tools/TRANSLATION_PIPELINE.md`

스테이지 1(통합 TSV 생성):

```powershell
python tools\translation_pipeline.py bootstrap-master
```

스테이지 2(빌드 입력 분해):

```powershell
python tools\translation_pipeline.py split-master --copy-reference
```

## Input Table Policy

- 번역 원본 테이블은 `.ref\TransProcess\source`를 공통으로 사용합니다.
- 입력 포맷은 TSV 우선(`*.tsv`)이며, 동일 stem에 TSV/CSV가 같이 있으면 TSV를 선택합니다.
- TSV가 없으면 CSV(`*.csv`)를 사용합니다.

## Output Overview

- Classic output:
  - `.ref\TransProcess\dist\windows_full\SUBTITLES.MIX`
  - `.ref\TransProcess\dist\subs_only\M_SUBTITLES.MIX`
- Enhanced output (default):
  - `.tmp\remaster_patch\loc_ko.txt`
  - `.tmp\remaster_patch\loc_it.txt`
  - `.tmp\remaster_patch\loc_it.tokenfix.txt`
  - `.tmp\remaster_patch\BladeRunnerEngine_poc_loc_it.kpf`
  - `.tmp\remaster_patch\fonts_poc_ko.kpf`
