# Blade Runner (1997) 한국어화 패치 엔진 작업 루트 (v1.0.1)

버전: `v1.0.1`  
기준 엔진: `ScummVM 2026.1.0` (Blade Runner 전용 커스텀 빌드)

이 폴더(`engine/`)는 **릴리즈 재현을 위한 엔진 작업 영역**입니다.

## 폴더 구성 (repo root 기준)

1. `engine/patches/`
- 패치 파일 및 패치 적용 대상 파일 세트.

2. `engine/scripts/`
- 빌드/패치/패키징 자동화 스크립트.

3. `engine/snapshots/ScummVM_BR_2026.1.0/`
- 패치 적용 커스텀 소스 스냅샷.

4. `engine/clean/` (선택)
- 사용자가 별도 준비한 clean 소스 보관 위치 권장.

5. `patch/Kor_Subs/`
- 최종 배포 리소스(자막, bat/ini, 라이선스, Windows 실행 파일).

## 빠른 시작 (Windows)

1. clean 소스에 패치 적용:
```bat
engine\scripts\apply_patch.bat C:\path\to\scummvm-2026.1.0_clean
```

2. 빌드 실행:
```bat
engine\scripts\build_msbuild_br.bat C:\path\to\scummvm-2026.1.0_clean
```

3. 배포 패키지 생성:
```powershell
powershell -ExecutionPolicy Bypass -File engine/scripts/package_release_v1.ps1 `
  -BuildRoot build_br `
  -ContentRoot patch/Kor_Subs `
  -ReleaseRoot patch/Release_Kor_Subs_v1.0.1 `
  -SourceRoot engine/snapshots/ScummVM_BR_2026.1.0
```

## 원본 소스 획득 기준

1. 공식 획득처(2026-02-07 확인):
- https://github.com/scummvm/scummvm/releases
- https://www.scummvm.org/downloads/
2. 재현용 기준 버전:
- GitHub 릴리즈 태그 `v2026.1.0`

## 참고 문서

1. 상세 가이드: `engine/README_PATCH.md`
2. 패치 파일 목록: `engine/PATCH_FILE_LIST.md`
3. 통합 패치: `engine/patches/diff/scummvm-2026.1.0_kor.patch`

## 주의

1. 본 패치는 비공식 사용자 제작물입니다.
2. Enhanced Edition은 지원 대상이 아닙니다.
3. 저장소에는 게임 원본 데이터가 포함되지 않습니다.

