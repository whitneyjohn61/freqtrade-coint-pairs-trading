# Pipe droplet_setup.sh to the Droplet over SSH (run from Windows PowerShell).
#
# Examples:
#   .\scripts\droplet_setup_from_local.ps1 -DropletHost 139.59.139.196 -ComposeProfile v02
#   .\scripts\droplet_setup_from_local.ps1 -DropletHost 165.227.165.131 -ComposeProfile v01
#
# Requires: OpenSSH client (ssh), SSH key access to the Droplet user (default root).

param(
    [Parameter(Mandatory = $true, HelpMessage = "Droplet public IPv4 or DNS name")]
    [string] $DropletHost,

    [ValidateSet("v01", "v02")]
    [string] $ComposeProfile = "v01",

    [string] $User = "root",

    [string] $RepoUrl = "https://github.com/whitneyjohn61/freqtrade-coint-pairs-trading.git",

    [string] $InstallDir = "",

    [switch] $SkipCompose
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
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
$remoteCmd += " bash -s"

$target = "${User}@${DropletHost}"

Write-Host "Running droplet_setup.sh on ${target} (profile ${ComposeProfile})..." -ForegroundColor Cyan
Get-Content -LiteralPath $scriptPath -Raw | ssh -T $target "$remoteCmd"
Write-Host "Finished." -ForegroundColor Green
