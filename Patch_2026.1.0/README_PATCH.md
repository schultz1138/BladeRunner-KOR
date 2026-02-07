# Blade Runner Korean Patch - Source Patch Guide (v1.0)

이 문서는 `Patch_2026.1.0` 폴더를 이용해  
빌드/패치/패키징을 재현하는 방법을 설명합니다.

## 소스 트리 역할 구분

1. `scummvm-2026.1.0_CLEAN`
- 사용자가 별도로 구해온 **무수정(upstream) ScummVM 2026.1.0 원본 소스 트리**입니다.
- 패치 생성(`make_diff.ps1`) 시 비교 기준(좌측)으로 사용됩니다.

2. `ScummVM_BR_2026.1.0`
- 이 저장소에 포함된 **이미 패치 적용된 커스텀 소스 트리**입니다.
- 기본 빌드/패키징 기준 소스로 사용됩니다.

## 원본 소스 획득(사용자 준비)

1. `scummvm-2026.1.0_CLEAN`은 사용자가 직접 받아와야 합니다.
2. 공식 획득처(2026-02-07 확인):
- https://github.com/scummvm/scummvm/releases
- https://www.scummvm.org/downloads/
3. 재현용 기준 버전:
- GitHub 태그 `v2026.1.0` (release title: `ScummVM 2026.1.0`)
4. 권장 절차:
- 다운로드한 원본을 `scummvm-2026.1.0_CLEAN` 폴더로 배치
- 원본 아카이브 SHA256 기록(릴리즈 노트/내부 문서)
- 필요 시 팀원은 같은 SHA256 파일만 사용

## 포함 내용

1. `diff/scummvm-2026.1.0_kor.patch`
- clean 소스에 적용 가능한 통합 패치.

2. `engines/bladerunner/...`
- 런타임 핵심 수정 파일(18개) 미러.

3. `build_msbuild_br.bat`
- Blade Runner 전용 솔루션 빌드 스크립트.

4. `make_diff.ps1`
- clean 소스와 수정 소스를 비교해 패치 재생성.

5. `package_release_v1.ps1`
- 빌드 산출물 + 리소스를 합쳐 배포 폴더 생성.

## 사전 준비

1. Visual Studio C++ x64 빌드 도구 설치.
2. `make_diff.ps1` 사용 시 Git 설치 및 PATH 등록 필요.
3. PowerShell(Windows PowerShell 5.1 이상 또는 PowerShell 7+) 사용.
4. 저장소 루트에 소스/리소스 준비:
- `ScummVM_2026.1.0` 또는 `ScummVM_BR_2026.1.0`
- `scummvm-2026.1.0_CLEAN` (사용자가 별도 준비한 무수정 원본 소스, 패치 비교용/선택)
- `Kor_Subs_v1.0`
5. 의존성 라이브러리는 **vcpkg 방식 권장**:
```bat
set VCPKG_ROOT=C:\path\to\vcpkg
%VCPKG_ROOT%\vcpkg install curl faad2 fluidsynth freetype fribidi giflib libflac libjpeg-turbo libmad libmikmod libmpeg2 libogg libpng libtheora libvorbis libvpx sdl2 sdl2-net zlib discord-rpc --triplet x64-windows
```
실측 참고:
- 일부 환경에서는 `libvpx` 빌드 실패가 발생할 수 있음.
- Blade Runner 패치 빌드 최소 필요 패키지(테스트 통과 기준):
```bat
%VCPKG_ROOT%\vcpkg install freetype fribidi libflac libjpeg-turbo libmad libmpeg2 libogg libpng libtheora libvorbis sdl2 sdl2-net zlib fluidsynth curl --triplet x64-windows
```
6. `SCUMMVM_LIBS` 환경변수 설정(vcpkg triplet 루트):
```bat
set SCUMMVM_LIBS=%VCPKG_ROOT%\installed\x64-windows
```

수동 빌드 대체 경로:
- 직접 라이브러리를 구성한 경우에도 `SCUMMVM_LIBS` 아래에 `include/lib/bin` 구조를 맞추면 빌드 가능.

## 1) 빌드

clean 소스 재현 경로(권장):
```bat
Patch_2026.1.0\apply_patch.bat C:\path\to\scummvm-2026.1.0_clean
Patch_2026.1.0\build_msbuild_br.bat C:\path\to\scummvm-2026.1.0_clean
```

기본 경로 자동 탐지 빌드:
```bat
Patch_2026.1.0\build_msbuild_br.bat
```

추가 옵션:
```bat
Patch_2026.1.0\build_msbuild_br.bat D:\Work\ScummVM_BR_2026.1.0
```

특징:
1. 개인 절대경로 하드코딩 없음.
2. `ScummVM_BR_2026.1.0` 우선, 없으면 `ScummVM_2026.1.0` 자동 탐지.
3. Visual Studio 설치 경로 자동 탐지(`vswhere`).
4. `SCUMMVM_LIBS`는 `vcpkg\installed\x64-windows` 지정 권장(루트 경로 아님).
5. 빌드 성공 시 런타임 DLL 15개를 `SCUMMVM_LIBS\bin`에서 `build_br/`로 자동 복사.
6. `SCUMMVM_LIBS`는 `include/lib/bin` 하위 구조가 모두 있어야 함.

## 2) 패치 적용 (Patch Application) - **New!**
 
 윈도우 환경에서 `git` 없이 패치를 적용하려면 아래 스크립트를 사용하세요.
 
 ```bat
 Patch_2026.1.0\apply_patch.bat <Clean_Source_Path>
 ```
 
 예시:
 ```bat
 Patch_2026.1.0\apply_patch.bat scummvm-2026.1.0_clean
 ```
 
- 이 스크립트는 런타임 핵심 18개 소스(`engines/bladerunner/...`)와 MSVC 빌드 설정 파일(`dists/msvc_br` 내 화이트리스트)을 복사합니다.
- 빌드 필수 생성/메타 파일(`dists/msvc_br/engines/plugins_table.h`, `detection_table.h`, `dists/scummvm_rc_engine_data*.rh`)도 함께 복사합니다.
- `msbuild_br.log` 같은 비결정적 빌드 로그 파일은 복사하지 않습니다.
 
 ## 3) 패치 재생성 (Patch Update) - 개발자용

```powershell
powershell -ExecutionPolicy Bypass -File Patch_2026.1.0/make_diff.ps1 `
  -CleanRoot scummvm-2026.1.0_CLEAN `
  -SourceRoot ScummVM_2026.1.0 `
  -OutPatch Patch_2026.1.0/diff/scummvm-2026.1.0_kor.patch
```

참고:
1. `-SourceRoot`를 생략하면 자동 탐지합니다.
2. 기본 출력 위치는 `Patch_2026.1.0/diff/scummvm-2026.1.0_kor.patch`입니다.

## 4) 배포 패키징

```powershell
powershell -ExecutionPolicy Bypass -File Patch_2026.1.0/package_release_v1.ps1 `
  -BuildRoot build_br `
  -ContentRoot Kor_Subs_v1.0 `
  -ReleaseRoot Release_Kor_Subs_v1.0 `
  -SourceRoot C:\path\to\scummvm-2026.1.0_clean
```

기본값을 그대로 쓰면 `-BuildRoot build_br`가 적용됩니다.
`ReleaseRoot`가 이미 존재하면 기존 폴더를 삭제 후 재생성합니다.

생성 결과:
1. `Release_Kor_Subs_v1.0/PC_Windows`
2. `Release_Kor_Subs_v1.0/Other_OS`
3. `SHA256SUMS.txt`, `RUNTIME_DLL_LIST.txt`, 릴리즈 노트

## 자주 막히는 포인트

1. `LNK1181: SDL2.lib`
- `SCUMMVM_LIBS`를 `%VCPKG_ROOT%\installed\x64-windows`로 지정했는지 확인.
- `%SCUMMVM_LIBS%\lib\SDL2.lib`가 실제로 존재하는지 확인.

2. 패키징에서 DLL 누락
- `build_msbuild_br.bat`가 정상 종료했는지(`MSBUILD EXIT 0`) 확인.
- `build_br`에 DLL 15개가 존재하는지 확인.

## 참고 문서

1. 패치 파일 목록: `Patch_2026.1.0/PATCH_FILE_LIST.md`
2. 통합 패치: `Patch_2026.1.0/diff/scummvm-2026.1.0_kor.patch`
3. 재현 점검 체크리스트: `REPRO_CHECKLIST.md`
4. 빌드 증적 템플릿: `BUILD_MANIFEST.txt`

## 저장소 정리 원칙

1. 재현/검증에 불필요한 빌드 산출물은 저장소에 포함하지 않음.
2. 대표 제외 항목:
- `build_br/`
- `Release_Kor_Subs_v1.0/`
- `ScummVM_BR_2026.1.0/dists/msvc_br/Releasex64/`
- `ScummVM_BR_2026.1.0/dists/msvc_br/msbuild_br.log`
- `ScummVM_BR_2026.1.0/plugin.exp`

## 유지보수 경계

1. 본 프로젝트의 재현성 책임 범위는 `Patch_2026.1.0`, `Kor_Subs_v1.0`, `ScummVM_BR_2026.1.0`에 한정됩니다.
2. 원본(`scummvm-2026.1.0_CLEAN`) 확보/보관/무결성 검증 책임은 사용자(빌더)에게 있습니다.
