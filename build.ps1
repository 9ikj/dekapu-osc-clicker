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

pyinstaller --noconfirm --clean --onefile --windowed --name dekapu-osc-clicker dekapu_osc_clicker.py

Write-Host ""
Write-Host "Build complete."
Write-Host "Output file: $PSScriptRoot\dist\dekapu-osc-clicker.exe"
