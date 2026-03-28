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

if (Test-Path dekapu-osc-clicker.spec) {
    Remove-Item dekapu-osc-clicker.spec -Force
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

try {
    pyinstaller --noconfirm --clean --onefile --windowed @runtimeHookArgs --name dekapu-osc-clicker dekapu_osc_clicker.py
}
finally {
    if ($runtimeHookPath -and (Test-Path $runtimeHookPath)) {
        Remove-Item $runtimeHookPath -Force
    }
}

Write-Host ""
Write-Host "Build complete."
Write-Host "Output file: $PSScriptRoot\dist\dekapu-osc-clicker.exe"
