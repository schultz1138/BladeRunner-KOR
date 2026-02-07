param(
    [string]$BuildRoot = "build_br",
    [string]$ContentRoot = "Kor_Subs_v1.0",
    [string]$ReleaseRoot = "Release_Kor_Subs_v1.0",
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Resolve-RepoPath([string]$path) {
    if ([System.IO.Path]::IsPathRooted($path)) {
        return $path
    }
    return (Join-Path $repoRoot $path)
}

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    foreach ($candidate in @("ScummVM_BR_2026.1.0", "ScummVM_2026.1.0")) {
        $probe = Join-Path $repoRoot $candidate
        if (Test-Path (Join-Path $probe "COPYING")) {
            $SourceRoot = $probe
            break
        }
    }
    if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
        $SourceRoot = Join-Path $repoRoot "ScummVM_2026.1.0"
    }
}
else {
    $SourceRoot = Resolve-RepoPath $SourceRoot
}

$BuildRoot = Resolve-RepoPath $BuildRoot
$ContentRoot = Resolve-RepoPath $ContentRoot
$ReleaseRoot = Resolve-RepoPath $ReleaseRoot
$releaseDate = Get-Date -Format "yyyy-MM-dd"

$runtimeDlls = @(
    "brotlicommon.dll",
    "brotlidec.dll",
    "bz2.dll",
    "FLAC.dll",
    "freetype.dll",
    "fribidi-0.dll",
    "jpeg62.dll",
    "libcurl.dll",
    "libpng16.dll",
    "ogg.dll",
    "SDL2.dll",
    "SDL2_net.dll",
    "vorbis.dll",
    "vorbisfile.dll",
    "zlib1.dll"
)

function Ensure-File([string]$path) {
    if (!(Test-Path $path)) {
        throw "Missing required file: $path"
    }
}

Ensure-File "$BuildRoot/scummvm.exe"
Ensure-File "$ContentRoot/Other_OS/SUBTITLES.MIX"
Ensure-File "$ContentRoot/PC_Windows/SUBTITLES.MIX"
Ensure-File "$ContentRoot/PC_Windows/scummvm.ini"
Ensure-File "$ContentRoot/PC_Windows/start.bat"
Ensure-File (Join-Path $SourceRoot "COPYING")
Ensure-File (Join-Path $SourceRoot "LICENSES/COPYING.OFL")

foreach ($dll in $runtimeDlls) {
    Ensure-File "$BuildRoot/$dll"
}

$releaseOther = Join-Path $ReleaseRoot "Other_OS"
$releaseWin = Join-Path $ReleaseRoot "PC_Windows"

if (Test-Path $ReleaseRoot) {
    Remove-Item -Path $ReleaseRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseOther -Force | Out-Null
New-Item -ItemType Directory -Path $releaseWin -Force | Out-Null

# Core payload
Copy-Item -Force "$ContentRoot/Other_OS/SUBTITLES.MIX" "$releaseOther/SUBTITLES.MIX"
Copy-Item -Force "$ContentRoot/PC_Windows/SUBTITLES.MIX" "$releaseWin/SUBTITLES.MIX"
Copy-Item -Force "$ContentRoot/PC_Windows/scummvm.ini" "$releaseWin/scummvm.ini"
Copy-Item -Force "$ContentRoot/PC_Windows/start.bat" "$releaseWin/start.bat"
Copy-Item -Force "$BuildRoot/scummvm.exe" "$releaseWin/scummvm.exe"

foreach ($dll in $runtimeDlls) {
    Copy-Item -Force "$BuildRoot/$dll" "$releaseWin/$dll"
}

# Root docs for package
Copy-Item -Force (Join-Path $SourceRoot "COPYING") "$ReleaseRoot/COPYING.txt"
Copy-Item -Force (Join-Path $SourceRoot "LICENSES/COPYING.OFL") "$ReleaseRoot/FONT_LICENSE.txt"

# Runtime DLL manifest
$dllManifest = @(
    "# Runtime DLL list (v1.0)",
    "# Build source: $BuildRoot",
    ""
) + $runtimeDlls
[System.IO.File]::WriteAllLines((Join-Path $ReleaseRoot "PC_Windows/RUNTIME_DLL_LIST.txt"), $dllManifest)

# Release note
$releaseNote = @(
    "# BladeRunner Korean Patch v1.0",
    "",
    "Date: $releaseDate",
    "Base: ScummVM 2026.1.0 (Blade Runner focused build)",
    "SourceRoot: $SourceRoot",
    "BuildRoot: $BuildRoot",
    "",
    "## Included",
    "- Korean subtitles (cutscene + in-game voice subtitles)",
    "- Korean UI rendering support on Windows build",
    "- UTF-8 UI rendering + legacy-byte fallback fixes",
    "",
    "## Windows payload",
    "- scummvm.exe",
    "- SUBTITLES.MIX",
    "- scummvm.ini",
    "- start.bat",
    "- 15 runtime DLLs (see PC_Windows/RUNTIME_DLL_LIST.txt)",
    "",
    "## Notes",
    "- Run with start.bat on Windows.",
    "- Enhanced Edition is not supported.",
    "- Source patch: Patch_2026.1.0/diff/scummvm-2026.1.0_kor.patch"
)
[System.IO.File]::WriteAllLines((Join-Path $ReleaseRoot "RELEASE_NOTES_v1.0.md"), $releaseNote)

# SHA256 sums
$hashLines = New-Object System.Collections.Generic.List[string]
$allFiles = Get-ChildItem -Path $ReleaseRoot -File -Recurse | Sort-Object FullName
foreach ($file in $allFiles) {
    if ($file.Name -eq "SHA256SUMS.txt") {
        continue
    }
    $h = Get-FileHash -Path $file.FullName -Algorithm SHA256
    $rel = $file.FullName.Substring((Resolve-Path $ReleaseRoot).Path.Length + 1).Replace("\", "/")
    [void]$hashLines.Add("$($h.Hash.ToLower())  $rel")
}
[System.IO.File]::WriteAllLines((Join-Path $ReleaseRoot "SHA256SUMS.txt"), $hashLines)

Write-Host "Release package assembled at: $ReleaseRoot"
Write-Host "Source root:" $SourceRoot
Write-Host "Build root:" $BuildRoot
Write-Host "Windows DLL count:" $runtimeDlls.Count
Write-Host "SHA256 entries:" $hashLines.Count
