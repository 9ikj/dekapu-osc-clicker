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

if (Test-Path massive_medal_pusher.spec) {
    Remove-Item massive_medal_pusher.spec -Force
}

pyinstaller --noconfirm --clean --onefile --windowed --name massive_medal_pusher vrchat_osc_clicker.py

Write-Host ""
Write-Host "Build complete."
Write-Host "Output file: $PSScriptRoot\dist\massive_medal_pusher.exe"
