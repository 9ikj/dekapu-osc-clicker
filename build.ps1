param(
    [string]$Version
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Error "PyInstaller is not installed. Run: pip install pyinstaller"
}

if (Test-Path build) {
    Remove-Item build -Recurse -Force
}

if (Test-Path dist) {
    Remove-Item dist -Recurse -Force
}

$runtimeHookPath = $null
$runtimeHookArgs = @()
if ($Version) {
    $runtimeHookPath = Join-Path $PSScriptRoot "build_version_hook.py"
    @"
import os
os.environ["DEKAPU_OSC_CLICKER_VERSION"] = r"$Version"
"@ | Set-Content -Path $runtimeHookPath -Encoding UTF8
    $runtimeHookArgs = @("--runtime-hook", $runtimeHookPath)
}

$assetsPath = Join-Path $PSScriptRoot "dekapu_osc_clicker\assets"
$templatesPath = Join-Path $PSScriptRoot "dekapu_osc_clicker\templates"
$iconPath = Join-Path $assetsPath "sp_assistant_icon.ico"
$pngIconPath = Join-Path $assetsPath "sp_assistant_icon.png"

python tools/generate_icon.py

$requiredFiles = @($iconPath, $pngIconPath, $templatesPath)
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        throw "Missing required asset: $file"
    }
}

python -m compileall dekapu_osc_clicker dekapu_osc_clicker.py

$pyinstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "dekapu-osc-clicker",
    "--add-data", "${assetsPath};dekapu_osc_clicker/assets",
    "--add-data", "${templatesPath};dekapu_osc_clicker/templates"
)

if (Test-Path $iconPath) {
    $pyinstallerArgs += @("--icon", $iconPath)
}

$pyinstallerArgs += $runtimeHookArgs
$pyinstallerArgs += "dekapu_osc_clicker.py"

try {
    pyinstaller @pyinstallerArgs
}
finally {
    if ($runtimeHookPath -and (Test-Path $runtimeHookPath)) {
        Remove-Item $runtimeHookPath -Force
    }
}

Write-Host ""
Write-Host "Build complete."
Write-Host "Output file: $PSScriptRoot\dist\dekapu-osc-clicker.exe"
