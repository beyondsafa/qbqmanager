# ===============================================
# PowerShell bootstrapper for qb-q-helper.py
# Ensures Scoop, Python, and dependencies are installed, then runs the helper
# ===============================================

# --- Set script directory and Python helper path ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$HelperScript = Join-Path $ScriptDir "qb-q-helper.py"

# --- Function to check if command exists ---
function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

Write-Host "=== qBittorrent Helper Bootstrap ==="

# 1. Ensure Scoop is installed
if (-not (Test-Command scoop)) {
    Write-Host "Scoop not found. Installing..."
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://get.scoop.sh')
} else {
    Write-Host "Scoop is already installed."
}

# 2. Ensure Python is installed
if (-not (Test-Command python)) {
    Write-Host "Python not found. Installing via Scoop..."
    scoop install python
} else {
    Write-Host "Python is already installed."
}

# 3. Ensure pip modules are installed
Write-Host "Checking required Python packages..."
$RequiredModules = @("requests")
foreach ($module in $RequiredModules) {
    $installed = & python -m pip show $module 2>$null
    if (-not $installed) {
        Write-Host "Installing $module..."
        & python -m pip install $module
    } else {
        Write-Host "$module is already installed."
    }
}

# 4. Run the Python helper
Write-Host "`nLaunching qb-q-helper.py..."
& python $HelperScript

Write-Host "`nPython helper finished (or running loop). Press Enter to exit..."
Read-Host
