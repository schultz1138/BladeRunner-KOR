# Remaster LOC Builder

`build_loc_ko.py` generates a Korean `loc` candidate for Blade Runner Enhanced by reusing
existing classic translation table files (`.tsv`/`.csv`) from `.ref/TransProcess/source`.

## Usage

```powershell
cd C:\Projects\BladeRunner-Kor
python tools\remaster\build_loc_ko.py
```

Default inputs:
- Template: `.tmp\kpf_unpacked\BladeRunnerEngine\text_like\loc_en.txt`
- Source: `.ref\TransProcess\source`

Default outputs:
- `.tmp\remaster_patch\loc_ko.txt`
- `.tmp\remaster_patch\loc_it.txt` (slot replacement copy)
- `.tmp\remaster_patch\build_report.md`
- `.tmp\remaster_patch\build_report.json`
- `.tmp\remaster_patch\markup_todo.csv`
- `.tmp\remaster_patch\ui_todo.csv`

## Unified Pipeline (Classic + Enhanced)

```powershell
cd C:\Projects\BladeRunner-Kor
python tools\pipeline.py build-all
```

Useful variants:

```powershell
# classic only
python tools\pipeline.py build-classic --profile both

# enhanced only
python tools\pipeline.py build-enhanced

# validate classic tables only
python tools\pipeline.py validate
```

## Build Test KPF

```powershell
python tools\remaster\patch_kpf_loc.py
```

Default output:
- `.tmp\remaster_patch\BladeRunnerEngine_poc_loc_it.kpf`

### Patch Fonts KPF For Korean Glyphs

```powershell
python tools\remaster\patch_kpf_fonts_ko.py
```

Default output:
- `.tmp\remaster_patch\fonts_poc_ko.kpf`
- Replaces `fonts/NotoSans-Regular.ttf`, `fonts/NotoSans-Bold.ttf`,
  `fonts/NotoSans-ExtraCondensedMedium.ttf`, `fonts/Montserrat-Regular.ttf` with `Kor_font.ttf`

## Auto Fix Markup Tokens

```powershell
python tools\remaster\fix_markup_tokens.py
```

Default outputs:
- `.tmp\remaster_patch\loc_it.tokenfix.txt`
- `.tmp\remaster_patch\token_glossary.csv`
- `.tmp\remaster_patch\token_fix_report.json`
- `.tmp\remaster_patch\token_fixed.csv`
- `.tmp\remaster_patch\token_unresolved.csv`

Notes:
- `token_glossary.csv`의 `KO` 열을 채우면 다음 실행 시 자동 반영됩니다.
- `--append-unresolved` 옵션을 주면 해결 불가 토큰도 문장 끝에 강제로 추가합니다.

## Auto Fill Glossary From Table Context

```powershell
python tools\remaster\fill_token_glossary.py
```

Notes:
- `loc_en.txt`(토큰 원문) + 생성된 `loc_it.txt`/`loc_ko.txt`(한국어 문맥)로 `token_glossary.csv`의 `KO`를 보수적으로 자동 채웁니다.
- `AutoSource`, `AutoConfidence`, `AutoEvidence` 컬럼이 함께 기록됩니다.
- `--refresh-auto`를 주면 기존 자동 채움 값을 지우고 다시 계산합니다.
- `--machine-translate-empty`를 주면 남은 빈 항목을 Google 번역으로 테스트용 채움합니다.

## Notes

- In-game subtitles and cutscene lines are imported automatically.
- UI import is partial (directly reusable groups + KIA + selected options labels).
- `markup_todo.csv` lists lines where EN markup tokens (`<...>`, `$...$`, `%...%`) were not preserved.
