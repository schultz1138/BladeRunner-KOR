# Pipeline Bundle For Repo Migration

이 폴더는 다른 저장소로 옮겨서 바로 사용할 수 있게 정리한 파이프라인 묶음입니다.

## Included

- `tools/`
  - `pipeline.py` (통합 엔트리)
  - `translation_pipeline.py` (extract/bootstrap/split)
  - `remaster/*.py` (Enhanced 빌드/토큰/패치)
- `.ref/TransProcess/tools/`
  - classic 빌드 파이프라인 + converter/validate/pack
- `.ref/TransProcess/assets/`
  - classic 빌드에 필요한 고정 리소스/폰트

## Recommended Placement In Target Repo

타깃 저장소 루트 기준 아래처럼 배치하면 경로 수정 없이 동작합니다.

```text
<target-repo>/
├─ tools/
└─ .ref/
   └─ TransProcess/
      ├─ tools/
      └─ assets/
```

## Quick Commands

```powershell
# 로컬 원문 추출
python tools\pipeline.py extract-local --classic-game-dir "C:\Games\BladeRunner\Classic"

# 로컬 추출 + 빌드
python tools\pipeline.py build-from-local --classic-game-dir "C:\Games\BladeRunner\Classic" --target classic

# master TSV 기준 빌드
python tools\pipeline.py build-from-master
```

## Public Repo Safety Check

```powershell
# 공개 저장소 반영 전: EN 컬럼 비어있는지 검사
python tools\check_public_tsv.py .tmp\translation_pipeline\master_translation.tsv
```

## Notes

- 원문 데이터는 `.tmp` 아래에만 생성하고 저장소에는 커밋하지 않는 것을 권장합니다.
- 클래식 원문 추출은 반드시 원본 `STARTUP.MIX`를 사용하세요.
- `SUBTITLES.MIX`는 패치 결과물일 수 있어 원문 EN 추출 기준으로 부적합할 수 있습니다.
