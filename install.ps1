# gitkey installer — Windows (PowerShell)
$ErrorActionPreference = "Stop"

$RepoUrl    = "git@github.com:geovanent/gitkey.git"
$InstallDir = Join-Path $env:USERPROFILE ".ssh\gitkey"
$BinDir     = Join-Path $env:USERPROFILE ".local\bin"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Info($msg)  { Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "! $msg" -ForegroundColor Yellow }
function Write-Die($msg)   { Write-Host "✗ $msg" -ForegroundColor Red; exit 1 }

function Test-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py -3" }
    Write-Die "Python 3 is required. Install from https://www.python.org/downloads/"
}

function Ensure-Repo {
    if (Test-Path (Join-Path $InstallDir ".git")) {
        Write-Info "Updating $InstallDir..."
        Push-Location $InstallDir
        try { git pull --ff-only 2>$null } catch { git pull 2>$null }
        Pop-Location
    }
    elseif (Test-Path (Join-Path $ScriptDir "switch_profile.py")) {
        $resolvedScript = (Resolve-Path $ScriptDir).Path
        $resolvedInstall  = (Resolve-Path $InstallDir -ErrorAction SilentlyContinue).Path
        if ($resolvedInstall -eq $resolvedScript) {
            Write-Info "Using existing installation at $InstallDir"
        }
        else {
            Write-Info "Copying from $ScriptDir..."
            New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
            Copy-Item -Path "$ScriptDir\*" -Destination $InstallDir -Recurse -Force `
                -Exclude @(".git", "settings.py", "repo_bindings.json")
        }
    }
    else {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Die "Git is required. Install Git for Windows: https://git-scm.com/download/win"
        }
        Write-Info "Cloning into $InstallDir..."
        New-Item -ItemType Directory -Force -Path (Split-Path $InstallDir) | Out-Null
        git clone $RepoUrl $InstallDir
    }
}

function Setup-Settings {
    $example  = Join-Path $InstallDir "settings-example.py"
    $settings = Join-Path $InstallDir "settings.py"
    if (-not (Test-Path $settings)) {
        Copy-Item $example $settings
        Write-Ok "Created $settings — edit it with your profiles"
    }
    else {
        Write-Ok "Keeping existing $settings"
    }
}

function Link-Cli {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $cmdPath = Join-Path $BinDir "gitkey.cmd"
    $pyScript = Join-Path $InstallDir "switch_profile.py"
    @"
@echo off
python "%pyScript%" %*
"@ | Set-Content -Path $cmdPath -Encoding ASCII
    Write-Ok "Created $cmdPath"
}

function Ensure-Path {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -split ";" | Where-Object { $_ -eq $BinDir }) {
        Write-Ok "PATH already includes $BinDir"
        return
    }
    $newPath = if ($userPath) { "$BinDir;$userPath" } else { $BinDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$BinDir;$env:Path"
    Write-Ok "Added $BinDir to user PATH (restart terminal if needed)"
}

function Verify-Install {
    $gitkey = Join-Path $BinDir "gitkey.cmd"
    if (-not (Test-Path $gitkey)) { Write-Die "gitkey.cmd was not created" }
    Write-Ok "gitkey is ready"
}

Write-Host ""
Write-Host "  gitkey installer (Windows)"
Write-Host "  ──────────────────────────"
Write-Host ""

Test-Python | Out-Null
Ensure-Repo
Setup-Settings
Link-Cli
Ensure-Path
Verify-Install

Write-Host ""
Write-Ok "Installation complete"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    1. Edit $InstallDir\settings.py"
Write-Host "    2. Create keys: ssh-keygen -t ed25519 -f `$env:USERPROFILE\.ssh\<profile>\id_ed25519"
Write-Host "    3. Run: gitkey -p <profile>   or   gitkey"
Write-Host ""
Write-Warn "For best SSH support on Windows, use Git Bash or WSL and run install.sh"
Write-Host ""
