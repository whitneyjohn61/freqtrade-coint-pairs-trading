# Pipe droplet_setup.sh to the Droplet over SSH (run from Windows PowerShell).
#
# Optional: scripts/local.env (gitignored) — set FT_DROPLET_HOST, FT_COMPOSE_PROFILE, FT_SSH_USER, etc.
#
# Examples:
#   .\scripts\droplet_setup_from_local.ps1 -DropletHost 139.59.139.196 -ComposeProfile v02
#   .\scripts\droplet_setup_from_local.ps1 -DropletHost 165.227.165.131 -ComposeProfile v01
#   # With local.env containing FT_DROPLET_HOST and FT_COMPOSE_PROFILE:
#   .\scripts\droplet_setup_from_local.ps1
#
# Requires: OpenSSH client (ssh), SSH key access to the Droplet user (default root).

param(
    [string] $DropletHost = "",

    [ValidateSet("v01", "v02")]
    [string] $ComposeProfile = "v01",

    [string] $User = "",

    [string] $RepoUrl = "",

    [string] $InstallDir = "",

    [string] $GitSshCommand = "",

    [switch] $SkipCompose
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

. (Join-Path $here "Import-DotEnv.ps1")
$localEnvPath = Join-Path $here "local.env"
if (Test-Path -LiteralPath $localEnvPath) {
    Import-DotEnv $localEnvPath
    Write-Host "Loaded: $localEnvPath" -ForegroundColor DarkGray
}

if ([string]::IsNullOrWhiteSpace($DropletHost)) {
    if ($env:FT_DROPLET_HOST) { $DropletHost = $env:FT_DROPLET_HOST }
}
if ([string]::IsNullOrWhiteSpace($DropletHost)) {
    throw "DropletHost is required (use -DropletHost IP or set FT_DROPLET_HOST in scripts/local.env)."
}

if (-not $PSBoundParameters.ContainsKey('ComposeProfile') -and $env:FT_COMPOSE_PROFILE) {
    $ComposeProfile = $env:FT_COMPOSE_PROFILE
}

if (-not $PSBoundParameters.ContainsKey('User')) {
    if ($env:FT_SSH_USER) { $User = $env:FT_SSH_USER }
}
if ([string]::IsNullOrWhiteSpace($User)) { $User = "root" }

if (-not $PSBoundParameters.ContainsKey('RepoUrl')) {
    if ($env:FT_REPO_URL) { $RepoUrl = $env:FT_REPO_URL }
}
if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
    $RepoUrl = "https://github.com/whitneyjohn61/freqtrade-coint-pairs-trading.git"
}

if (-not $PSBoundParameters.ContainsKey('InstallDir')) {
    if ($env:FT_INSTALL_DIR) { $InstallDir = $env:FT_INSTALL_DIR }
}

if (-not $PSBoundParameters.ContainsKey('GitSshCommand')) {
    if ($env:FT_GIT_SSH_COMMAND) { $GitSshCommand = $env:FT_GIT_SSH_COMMAND }
}

$scriptPath = Join-Path $here "droplet_setup.sh"

if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing script: $scriptPath"
}

function BashSingleQuote([string]$s) {
    return "'" + ($s -replace "'", "'\''") + "'"
}

$remoteCmd = "export FT_COMPOSE_PROFILE=$(BashSingleQuote $ComposeProfile); export FT_REPO_URL=$(BashSingleQuote $RepoUrl);"
if ($InstallDir) {
    $remoteCmd += " export FT_INSTALL_DIR=$(BashSingleQuote $InstallDir);"
}
if ($SkipCompose) {
    $remoteCmd += " export FT_SKIP_COMPOSE=1;"
}
if ($GitSshCommand) {
    $remoteCmd += " export FT_GIT_SSH_COMMAND=$(BashSingleQuote $GitSshCommand);"
}
$remoteCmd += " bash -s"

$target = "${User}@${DropletHost}"

Write-Host "Running droplet_setup.sh on ${target} (profile ${ComposeProfile})..." -ForegroundColor Cyan
$scriptBody = (Get-Content -LiteralPath $scriptPath -Raw) -replace "`r`n", "`n" -replace "`r", "`n"
$scriptBody | ssh -T $target "$remoteCmd"
Write-Host "Finished." -ForegroundColor Green
