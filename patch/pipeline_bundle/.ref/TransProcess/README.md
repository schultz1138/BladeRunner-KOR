# TransProcess

Blade Runner(ScummVM) 한국어화 리소스를 한 폴더에서 관리/번역/변환/패킹하기 위한 작업 루트입니다.

## 1) 핵심 목표
- UI 번역 테이블(TSV/CSV) 수정 -> TRE 변환
- 컷씬 자막 테이블(TSV/CSV) 수정 -> TRE 변환
- 인게임 음성자막(INGQUO.tsv/INGQUO.csv) 수정 -> TRE 변환
- 최종 `SUBTITLES.MIX`(Windows full) / `M_SUBTITLES.MIX`(subs only) 생성

## 2) 빠른 시작
작업 루트: `TransProcess` 폴더

```powershell
cd <TransProcess_폴더_경로>
python tools\pipeline.py validate
python tools\pipeline.py build-all
```

산출물:
- `dist\windows_full\SUBTITLES.MIX` : UI + 컷씬 + 인게임 자막 포함
- `dist\subs_only\M_SUBTITLES.MIX` : 컷씬 + 인게임 자막만 포함 (UI 제외)

## 3) 번역 수정 위치
- UI: `source\ui\ko_work\*.tsv` (`.csv`도 지원)
- 컷씬: `source\cutscene\ko_work\*.tsv` (`.csv`도 지원)
- 인게임: `source\ingame\ko_work\INGQUO.tsv` (`.csv`도 지원)

참고 원문:
- UI 원문: `source\ui\en_original\*.tsv`/`*.csv`
- 인게임 기준셋(검증용): `source\ingame\en_reference\INGQUO.tsv`/`INGQUO.csv`
- 원본 스프레드시트 보관: `source\reference_xlsx\*.xlsx`

## 4) 폴더 개요
상세 설명: `docs\FOLDER_MAP.md`

- `assets\fixed` : `SBTLVERS.TRE`, `EXTRA.TRE`, `SUBTLS_E.FON`
- `assets\fonts` : `Kor_font.ttf`, `Font_LICENSE.txt`
- `tools\converters` : 테이블(TSV/CSV) -> TRE 변환기
- `tools\validate` : 테이블 무결성 검증기
- `tools\pack` : MIX 패커
- `tools\pipeline.py` : 전체 자동 파이프라인
- `build` : 중간 산출물(TRE, pack_input, 로그/리포트)
- `dist` : 최종 MIX 산출물

## 5) 운영 원칙
- 인게임 테이블은 `Filename`(NN-NNNN.AUD)를 기준으로 TRE id를 계산합니다.
- 행 순서가 바뀌어도 id 기반으로 매핑되므로, 행 누락/중복만 방지하면 싱크가 무너지지 않습니다.
- `validate` 단계에서 파일명 규칙/중복/기준셋 차이를 먼저 차단합니다.

## 6) 자주 쓰는 명령
```powershell
# 검증만
python tools\pipeline.py validate

# Windows full만
python tools\pipeline.py build --profile windows_full

# Subtitles only만
python tools\pipeline.py build --profile subs_only

# 둘 다
python tools\pipeline.py build-all

# (선택) 소스/산출 루트 오버라이드
python tools\pipeline.py build --profile subs_only --source-root C:\path\to\source_split --work-root C:\path\to\classic_work
```

## 7) 문제 발생 시
`docs\TROUBLESHOOTING.md` 확인.
