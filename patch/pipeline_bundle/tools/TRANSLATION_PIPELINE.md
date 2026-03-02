# Translation Pipeline Roadmap

목표:
- 원문 리소스를 저장소에 포함하지 않고, 사용자 로컬에서만 추출/패치.
- 번역자는 단일 TSV(`master_translation.tsv`)를 수정.
- 빌드 단계에서 클래식/인핸스드 출력물로 자동 분해 및 패킹.

## Stage 1 (현재 구현)

통합 TSV 생성:

```powershell
cd C:\Projects\BladeRunner-Kor
python tools\translation_pipeline.py bootstrap-master
```

기본 산출물:
- `.tmp\translation_pipeline\master_translation.tsv`
- `.tmp\translation_pipeline\master_report.json`

기본 컬럼:
- `uid`: 안정 식별자 (`ui:ACTORS:0`, `cut:INTRO:16-55`, `ing:INGQUO:00-0000.AUD`)
- `domain`: `ui` / `cutscene` / `ingame`
- `table`, `key`
- 구조 보조 컬럼: `filename`, `frame_start`, `frame_end`, `actor`
- `token_sig`: EN 토큰 시그니처(`<...>`, `$...$`, `%...%`)
- `en`, `ko`, `status`, `note`

EN 제외(배포용 샘플) 생성:

```powershell
python tools\translation_pipeline.py bootstrap-master --without-en
```

## Stage 2 (현재 구현)

`master_translation.tsv`를 다시 빌드 입력 테이블로 분해:

```powershell
python tools\translation_pipeline.py split-master --copy-reference
```

기본 산출물:
- `.tmp\translation_pipeline\source_split\ui\ko_work\*.tsv`
- `.tmp\translation_pipeline\source_split\cutscene\ko_work\*.tsv`
- `.tmp\translation_pipeline\source_split\ingame\ko_work\INGQUO.tsv`
- `.tmp\translation_pipeline\split_report.json`

옵션:
- `--translated-only`: `status=translated` 행만 분해
- `--skip-empty-ko`: KO 빈 행 제외

참고:
- `--copy-reference`를 사용하면 `ui/en_original`, `cutscene/en_reference`, `ingame/en_reference`도 같이 복사됩니다.
- 생성된 `source_split` 루트는 remaster 빌더 입력으로 바로 사용 가능합니다.
  - `python tools\remaster\build_loc_ko.py --transprocess-source .tmp\translation_pipeline\source_split`

## Stage 3 (현재 구현)

마스터 TSV 기반 연속 빌드:

```powershell
python tools\pipeline.py build-from-master
```

대표 옵션:
- 클래식만: `python tools\pipeline.py build-from-master --target classic --classic-profile subs_only`
- 인핸스드만: `python tools\pipeline.py build-from-master --target enhanced`
- `master_translation.tsv` 재생성 포함:
  - `python tools\pipeline.py build-from-master --bootstrap-master`

동작:
1) 필요 시 `bootstrap-master` 실행
2) `split-master` 실행 (`source_split` 생성)
3) `source_split`을 입력으로 클래식/인핸스드 빌드 실행

## Stage 4 (현재 구현)

로컬 원문 추출:

```powershell
python tools\translation_pipeline.py extract-local ^
  --classic-game-dir "C:\Games\BladeRunner\Classic" ^
  --enhanced-engine-kpf "C:\Games\BladeRunner\BladeRunnerEngine.kpf"
```

기본 산출물:
- `.tmp\translation_pipeline\local_extract\source\...` (ui/cutscene/ingame 테이블)
- `.tmp\translation_pipeline\local_extract\enhanced\loc_en.txt`
- `.tmp\translation_pipeline\extract_report.json`

원클릭 빌드(추출 + master 재생성 + 분해 + 빌드):

```powershell
python tools\pipeline.py build-from-local ^
  --classic-game-dir "C:\Games\BladeRunner\Classic" ^
  --enhanced-engine-kpf "C:\Games\BladeRunner\BladeRunnerEngine.kpf" ^
  --target both --classic-profile subs_only
```

주의:
- 클래식 입력은 `STARTUP.MIX`에서 읽습니다.
- 원문 데이터는 `.tmp` 아래에만 생성하고 저장소에는 커밋하지 않습니다.
