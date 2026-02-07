# Blade Runner (1997) 한국어화 패치 v1.0 RC

버전: `v1.0 RC`  
기준 엔진: `ScummVM_BR 2026.1.0` (Blade Runner 전용 커스텀 빌드 기준)

이 폴더는 **릴리즈 재현을 위한 소스/스크립트 작업본**입니다.

## 폴더 구성

1. `Patch_2026.1.0/`
- 소스 코드 패치 세트와 빌드/패키징 스크립트.

2. `Kor_Subs_v1.0/`
- 빌드 사용자용 리소스 패키지(자막/MIX, ini, start.bat).
- `scummvm.exe`, DLL은 의도적으로 제외됨.

3. `ScummVM_BR_2026.1.0/`
- 재현 가능한 소스 스냅샷(경량화본).
- 불필요한 빌드 산출물/캐시는 제외됨.

## 재현성 기준

1. 기본 빌드 출력 경로는 `build_br/`로 고정.
2. 패키징 기본 입력도 `build_br/`를 사용.
3. 패치 적용(`apply_patch.bat`)은 런타임 핵심 18개 파일 + MSVC 빌드 설정 파일만 복사.
4. `make_diff.ps1`는 `git` 필요(패치 생성 전용).

## 소스 트리 역할 구분

1. `scummvm-2026.1.0_CLEAN`
- 사용자가 별도로 구해온 **무수정(upstream) ScummVM 2026.1.0 원본 소스 트리**를 의미.
- 패치 생성/검증 시 기준 비교 대상으로 사용.

2. `ScummVM_BR_2026.1.0`
- 이 저장소에 포함된 **이미 패치 적용된 커스텀 소스 트리**를 의미.
- 빌드 및 패키징의 기본 소스 기준으로 사용.

## 원본 소스 획득 및 고정

1. 원본 소스는 사용자가 직접 준비해야 합니다(이 저장소에 포함하지 않음).
2. 공식 획득처(2026-02-07 확인):
- https://github.com/scummvm/scummvm/releases
- https://www.scummvm.org/downloads/
3. 재현용 기준 버전:
- GitHub 릴리즈 태그 `v2026.1.0` (release title: `ScummVM 2026.1.0`)
4. 권장:
- 내려받은 원본 아카이브 파일의 SHA256을 기록하고, 추후 동일 파일인지 검증.

## 빌드 빠른 시작 (Windows)

1. Visual Studio C++ x64 빌드 도구 설치.
2. 의존성 라이브러리는 **vcpkg 방식 권장**:
```bat
set VCPKG_ROOT=C:\path\to\vcpkg
%VCPKG_ROOT%\vcpkg install curl faad2 fluidsynth freetype fribidi giflib libflac libjpeg-turbo libmad libmikmod libmpeg2 libogg libpng libtheora libvorbis libvpx sdl2 sdl2-net zlib discord-rpc --triplet x64-windows
```
   - 실측상 일부 환경에서 `libvpx` 빌드가 실패할 수 있습니다.
   - Blade Runner 패치 빌드에 필요한 최소 패키지(테스트 통과 기준):
```bat
%VCPKG_ROOT%\vcpkg install freetype fribidi libflac libjpeg-turbo libmad libmpeg2 libogg libpng libtheora libvorbis sdl2 sdl2-net zlib fluidsynth curl --triplet x64-windows
```
3. `SCUMMVM_LIBS`를 vcpkg triplet 루트로 설정:
```bat
set SCUMMVM_LIBS=%VCPKG_ROOT%\installed\x64-windows
```
4. clean 소스 기준이면 먼저 패치 적용:
```bat
Patch_2026.1.0\apply_patch.bat C:\path\to\scummvm-2026.1.0_clean
```
5. 빌드 실행:
```bat
Patch_2026.1.0\build_msbuild_br.bat C:\path\to\scummvm-2026.1.0_clean
```
   - 성공 시 `build_br/`에 `scummvm.exe`와 런타임 DLL 15개가 함께 생성됩니다.
6. 배포 폴더 생성(기본 BuildRoot=`build_br`):
```powershell
powershell -ExecutionPolicy Bypass -File Patch_2026.1.0\package_release_v1.ps1 -SourceRoot C:\path\to\scummvm-2026.1.0_clean
```
   - 스크립트는 `Release_Kor_Subs_v1.0`를 매번 새로 생성(기존 폴더 삭제 후 재생성)합니다.

대체 경로(고급 사용자): 수동으로 라이브러리를 구성한 경우에도 `SCUMMVM_LIBS` 아래에 `include/lib/bin` 구조를 맞추면 빌드 가능합니다.

## 문제 해결

1. `LNK1181: SDL2.lib` 오류
- `SCUMMVM_LIBS`가 vcpkg 루트가 아닌 `installed\x64-windows`를 가리키는지 확인.
- `%SCUMMVM_LIBS%\lib\SDL2.lib` 존재 여부 확인.

2. 런타임 DLL 누락 오류
- `build_msbuild_br.bat`는 `%SCUMMVM_LIBS%\bin`에서 15개 DLL을 복사합니다.
- `%SCUMMVM_LIBS%\bin`이 비어 있으면 vcpkg 설치가 불완전한 상태입니다.

3. 패키징 시 파일 누락 오류
- 반드시 빌드가 먼저 성공해야 하며, `build_br\scummvm.exe`와 DLL 15개가 있어야 합니다.

## 라이선스

1. ScummVM 엔진: GPL 계열 라이선스(원본 프로젝트 정책 준수).
2. 폰트 라이선스: `Kor_Subs_v1.0/FONT_LICENSE.txt` 참고.

## 운영 문서

1. 재현 점검 체크리스트: `REPRO_CHECKLIST.md`
2. 빌드 증적 템플릿: `BUILD_MANIFEST.txt`

## 업로드 전 정리 기준

1. GitHub 업로드 시 빌드 산출물/캐시는 제외:
- `build_br/`
- `Release_Kor_Subs_v1.0/`
- `ScummVM_BR_2026.1.0/dists/msvc_br/Releasex64/`
- `ScummVM_BR_2026.1.0/dists/msvc_br/msbuild_br.log`
- `ScummVM_BR_2026.1.0/plugin.exp`
2. 위 항목은 `.gitignore`로 제외되며, 저장소에는 재현/검증용 소스/스크립트/문서만 유지.

## 주의

1. 본 패치는 비공식 사용자 제작물입니다.
2. Enhanced Edition은 지원 대상이 아닙니다.
3. 이 저장소에는 게임 원본 데이터가 포함되어 있지 않습니다.
