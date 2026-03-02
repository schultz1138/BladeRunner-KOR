Place a clean ScummVM 2026.1.0 source tree at:
  ..\scummvm-2026.1.0_CLEAN

Then run from repository root:
  powershell -ExecutionPolicy Bypass -File Patch_2026.1.0\make_diff.ps1

It writes:
  Patch_2026.1.0\diff\scummvm-2026.1.0_kor.patch

Notes:
- The script builds patch from 18 core Blade Runner runtime files only.
- `vcpkg.json`, generated headers, and local build artifacts are excluded.
- On Windows CRLF trees, verify/apply with:
  git apply --ignore-space-change --ignore-whitespace --check --directory=scummvm-2026.1.0_CLEAN Patch_2026.1.0/diff/scummvm-2026.1.0_kor.patch
