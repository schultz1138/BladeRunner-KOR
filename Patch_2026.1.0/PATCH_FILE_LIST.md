# PATCH File List (v1.0 / 2026-02-06)

이 문서는 `scummvm-2026.1.0_kor.patch`를 구성하는 기준 파일 목록입니다.

## Core runtime files (필수 18개)

1. `engines/bladerunner/bladerunner.cpp`
2. `engines/bladerunner/bladerunner.h`
3. `engines/bladerunner/dialogue_menu.cpp`
4. `engines/bladerunner/subtitles.cpp`
5. `engines/bladerunner/ui/end_credits.cpp`
6. `engines/bladerunner/ui/esper.cpp`
7. `engines/bladerunner/ui/kia.cpp`
8. `engines/bladerunner/ui/kia_section_clues.cpp`
9. `engines/bladerunner/ui/kia_section_crimes.cpp`
10. `engines/bladerunner/ui/kia_section_diagnostic.cpp`
11. `engines/bladerunner/ui/kia_section_pogo.cpp`
12. `engines/bladerunner/ui/kia_section_save.cpp`
13. `engines/bladerunner/ui/kia_section_settings.cpp`
14. `engines/bladerunner/ui/kia_section_suspects.cpp`
15. `engines/bladerunner/ui/scores.cpp`
16. `engines/bladerunner/ui/ui_dropdown.cpp`
17. `engines/bladerunner/ui/ui_image_picker.cpp`
18. `engines/bladerunner/ui/ui_scroll_box.cpp`

## Optional reproducibility file (선택)

1. `vcpkg.json`
- 목적: 빌드 시점 의존성 baseline 재현.
- 런타임 동작 수정과 직접 관련 없음.

## Patch에서 제외하는 항목

1. `dists/msvc_br/engines/detection_table.h`
2. `dists/msvc_br/engines/plugins_table.h`
3. `vcpkg_installed/**`
4. 빌드 산출물(`*.obj`, `*.pdb`, `Releasex64/**` 등)
5. IDE/개인 환경 파일(`.vscode/**`, 로컬 세이브 등)

## 패치 생성 예시

```powershell
powershell -ExecutionPolicy Bypass -File Patch_2026.1.0/make_diff.ps1 `
  -CleanRoot scummvm-2026.1.0_CLEAN `
  -SourceRoot ScummVM_2026.1.0 `
  -OutPatch Patch_2026.1.0/diff/scummvm-2026.1.0_kor.patch
```
