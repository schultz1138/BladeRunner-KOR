# Blade Runner Korean Patch - Source Patch Guide (v1.0.1)

이 문서는 현행 저장소 구조(`engine/`, `patch/`) 기준으로  
빌드/패치/패키징 재현 절차를 설명합니다.

## 기준 폴더 (repo root 기준)

1. `engine/clean/scummvm-2026.1.0_CLEAN` (선택)
- 사용자가 별도로 준비한 무수정(upstream) ScummVM 2026.1.0 소스.
- 패치 생성(`make_diff.ps1`) 시 비교 기준으로 사용.

2. `engine/snapshots/ScummVM_BR_2026.1.0`
- 저장소에 포함된 패치 적용 커스텀 소스 스냅샷.
- 기본 빌드 소스.

3. `engine/patches`
- 패치 파일과 적용 대상 파일(런타임 18개 + MSVC 설정 파일).

4. `engine/scripts`
- 자동화 스크립트.
  - `apply_patch.bat`
  - `build_msbuild_br.bat`
  - `make_diff.ps1`
  - `package_release_v1.ps1`

5. `patch/Kor_Subs`
- 배포 리소스(자막, ini/bat, 라이선스, Windows 실행 파일 등).

## 원본 소스 획득(사용자 준비)

1. 공식 획득처(2026-02-07 확인):
- https://github.com/scummvm/scummvm/releases
- https://www.scummvm.org/downloads/
2. 재현 기준 버전:
- GitHub 태그 `v2026.1.0` (release title: `ScummVM 2026.1.0`)

## 사전 준비

1. Visual Studio C++ x64 빌드 도구 설치.
2. `make_diff.ps1` 사용 시 Git 설치 및 PATH 등록 필요.
3. PowerShell(Windows PowerShell 5.1 이상 또는 PowerShell 7+) 사용.
4. `SCUMMVM_LIBS`는 `include/lib/bin` 구조를 갖는 경로여야 함.

권장(vcpkg):
```bat
set VCPKG_ROOT=C:\path\to\vcpkg
%VCPKG_ROOT%\vcpkg install freetype fribidi libflac libjpeg-turbo libmad libmpeg2 libogg libpng libtheora libvorbis sdl2 sdl2-net zlib fluidsynth curl --triplet x64-windows
set SCUMMVM_LIBS=%VCPKG_ROOT%\installed\x64-windows
```

## 1) 패치 적용

```bat
engine\scripts\apply_patch.bat C:\path\to\scummvm-2026.1.0_clean
```

- 런타임 핵심 18개 소스 + `dists/msvc_br` 빌드 설정 파일을 복사합니다.

## 2) 빌드

clean 소스 기준:
```bat
engine\scripts\build_msbuild_br.bat C:\path\to\scummvm-2026.1.0_clean
```

자동 탐지 기준 빌드:
```bat
engine\scripts\build_msbuild_br.bat
```

특징:
1. 기본 탐지 우선순위: `engine/snapshots/ScummVM_BR_2026.1.0` -> `ScummVM_2026.1.0`
2. 성공 시 `build_br/`에 `scummvm.exe` + 런타임 DLL 15개 생성
3. Visual Studio 설치 경로는 `vswhere`로 자동 탐지

## 3) 패치 재생성 (개발자용)

```powershell
powershell -ExecutionPolicy Bypass -File engine/scripts/make_diff.ps1 `
  -CleanRoot engine/clean/scummvm-2026.1.0_CLEAN `
  -SourceRoot engine/snapshots/ScummVM_BR_2026.1.0 `
  -OutPatch engine/patches/diff/scummvm-2026.1.0_kor.patch
```

참고:
1. `-SourceRoot` 생략 시 자동 탐지합니다.
2. `-OutPatch` 생략 시 기본 출력은 `engine/patches/scummvm-2026.1.0_kor.patch` 입니다.

## 4) 배포 패키징

```powershell
powershell -ExecutionPolicy Bypass -File engine/scripts/package_release_v1.ps1 `
  -BuildRoot build_br `
  -ContentRoot patch/Kor_Subs `
  -ReleaseRoot patch/Release_Kor_Subs_v1.0.1 `
  -SourceRoot engine/snapshots/ScummVM_BR_2026.1.0
```

생성 결과:
1. `patch/Release_Kor_Subs_v1.0.1/PC_Windows`
2. `patch/Release_Kor_Subs_v1.0.1/Other_OS`
3. `SHA256SUMS.txt`, `RUNTIME_DLL_LIST.txt`, 릴리즈 노트
4. `-ReleaseRoot`를 생략하면 스크립트 기본값은 `patch/Release_Kor_Subs_v1.0` 입니다.

주의:
1. 현재 `package_release_v1.ps1`은 `PC_Windows/scummvm.ini`, `build_br/scummvm.exe` 기준으로 동작합니다.
2. `scummvm-k.ini/scummvm-k.exe` 체계를 그대로 유지하려면 스크립트 수정 또는 파일명 정합화가 필요합니다.

## 자주 막히는 포인트

1. `LNK1181: SDL2.lib`
- `SCUMMVM_LIBS=%VCPKG_ROOT%\installed\x64-windows` 확인
- `%SCUMMVM_LIBS%\lib\SDL2.lib` 존재 확인

2. DLL 누락
- `build_msbuild_br.bat` 종료 코드(`MSBUILD EXIT 0`) 확인
- `build_br/`에 DLL 15개 존재 여부 확인

## 참고 문서

1. 패치 파일 목록: `engine/PATCH_FILE_LIST.md`
2. 통합 패치: `engine/patches/diff/scummvm-2026.1.0_kor.patch`
3. 엔진 루트 안내: `engine/README_Patch_Root.md`

## 저장소 정리 기준

1. 재현에 불필요한 빌드 산출물은 저장소에 포함하지 않음.
2. 대표 제외 항목:
- `build_br/`
- `patch/Release_Kor_Subs_v1.0.1/`
- `engine/snapshots/ScummVM_BR_2026.1.0/dists/msvc_br/Releasex64/`
- `engine/snapshots/ScummVM_BR_2026.1.0/dists/msvc_br/msbuild_br.log`
- `engine/snapshots/ScummVM_BR_2026.1.0/plugin.exp`

