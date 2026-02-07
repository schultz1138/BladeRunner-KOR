param(
    [string]$CleanRoot = "scummvm-2026.1.0_CLEAN",
    [string]$SourceRoot = "",
    [string]$OutPatch = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-RelativePathCompat([string]$basePath, [string]$targetPath) {
    try {
        return [System.IO.Path]::GetRelativePath($basePath, $targetPath)
    }
    catch {
        $baseUri = [Uri]((Resolve-Path $basePath).Path.TrimEnd('\') + '\')
        $targetUri = [Uri]((Resolve-Path $targetPath).Path)
        $relUri = $baseUri.MakeRelativeUri($targetUri)
        return [Uri]::UnescapeDataString($relUri.ToString()).Replace("/", "\")
    }
}

function Resolve-RepoPath([string]$path) {
    if ([System.IO.Path]::IsPathRooted($path)) {
        return $path
    }
    return (Join-Path $repoRoot $path)
}

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    foreach ($candidate in @("ScummVM_BR_2026.1.0", "ScummVM_2026.1.0")) {
        $probe = Join-Path $repoRoot $candidate
        if (Test-Path (Join-Path $probe "engines/bladerunner/bladerunner.cpp")) {
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

$CleanRoot = Resolve-RepoPath $CleanRoot

if ([string]::IsNullOrWhiteSpace($OutPatch)) {
    $OutPatch = Join-Path $PSScriptRoot "diff/scummvm-2026.1.0_kor.patch"
}
elseif (-not [System.IO.Path]::IsPathRooted($OutPatch)) {
    $OutPatch = Join-Path $repoRoot $OutPatch
}

$outDir = Split-Path -Parent $OutPatch
if (!(Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    throw "git command not found. Install Git and ensure 'git' is available in PATH."
}

$cleanPrefix = (Get-RelativePathCompat $repoRoot $CleanRoot).Replace("\", "/")
$sourcePrefix = (Get-RelativePathCompat $repoRoot $SourceRoot).Replace("\", "/")

$files = @(
    "engines/bladerunner/bladerunner.cpp",
    "engines/bladerunner/bladerunner.h",
    "engines/bladerunner/dialogue_menu.cpp",
    "engines/bladerunner/subtitles.cpp",
    "engines/bladerunner/ui/end_credits.cpp",
    "engines/bladerunner/ui/esper.cpp",
    "engines/bladerunner/ui/kia.cpp",
    "engines/bladerunner/ui/kia_section_clues.cpp",
    "engines/bladerunner/ui/kia_section_crimes.cpp",
    "engines/bladerunner/ui/kia_section_diagnostic.cpp",
    "engines/bladerunner/ui/kia_section_pogo.cpp",
    "engines/bladerunner/ui/kia_section_save.cpp",
    "engines/bladerunner/ui/kia_section_settings.cpp",
    "engines/bladerunner/ui/kia_section_suspects.cpp",
    "engines/bladerunner/ui/scores.cpp",
    "engines/bladerunner/ui/ui_dropdown.cpp",
    "engines/bladerunner/ui/ui_image_picker.cpp",
    "engines/bladerunner/ui/ui_scroll_box.cpp"
)

$all = New-Object System.Collections.Generic.List[string]

Push-Location $repoRoot
try {
    foreach ($rel in $files) {
        $leftAbs = Join-Path $CleanRoot $rel
        $rightAbs = Join-Path $SourceRoot $rel

        if (!(Test-Path $leftAbs)) {
            throw "Missing clean file: $leftAbs"
        }
        if (!(Test-Path $rightAbs)) {
            throw "Missing source file: $rightAbs"
        }

        $left = (Get-RelativePathCompat $repoRoot $leftAbs).Replace("\", "/")
        $right = (Get-RelativePathCompat $repoRoot $rightAbs).Replace("\", "/")

        $raw = & git -c core.safecrlf=false diff --no-index -- "$left" "$right" 2>$null
        if ($LASTEXITCODE -eq 0) {
            continue
        }
        if ($LASTEXITCODE -gt 1) {
            throw "git diff failed for $rel (exit=$LASTEXITCODE)"
        }

        $norm = $raw | ForEach-Object {
            $_.Replace("a/$cleanPrefix/", "a/").Replace("b/$sourcePrefix/", "b/")
        }

        foreach ($line in $norm) {
            [void]$all.Add($line)
        }
        [void]$all.Add("")
    }
}
finally {
    Pop-Location
}

if ($all.Count -eq 0) {
    throw "No differences found for selected files."
}

$text = ($all -join [Environment]::NewLine)
if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) {
    $text = $text.Substring(1)
}

[System.IO.File]::WriteAllText(
    $OutPatch,
    $text,
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "Patch written:" $OutPatch
Write-Host "Source root:" $SourceRoot
Write-Host "Diff sections:" (($all | Select-String -Pattern '^diff --git ' | Measure-Object).Count)
