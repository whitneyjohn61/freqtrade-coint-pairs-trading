# SSH to both Droplets and run droplet_status_remote.sh for a single status summary.
#
# Optional: copy scripts/local.env.example -> scripts/local.env (gitignored) and set FT_V01_HOST, FT_V02_HOST, passwords, etc.
#
# Usage (from repo root):
#   .\scripts\droplet_status_from_local.ps1
#   .\scripts\droplet_status_from_local.ps1 -V01Host 165.227.165.131 -V02Host 139.59.139.196
#   .\scripts\droplet_status_from_local.ps1 -SkipTrades
#   .\scripts\droplet_status_from_local.ps1 -LogTail 25

param(
    [string] $V01Host = "",
    [string] $V02Host = "",
    [string] $User = "",
    [string] $RepoRoot = "",
    [int] $LogTail = 18,
    [switch] $SkipTrades
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

. (Join-Path $here "Import-DotEnv.ps1")
$localEnvPath = Join-Path $here "local.env"
if (Test-Path -LiteralPath $localEnvPath) {
    Import-DotEnv $localEnvPath
    Write-Host "Loaded: $localEnvPath" -ForegroundColor DarkGray
}

if (-not $PSBoundParameters.ContainsKey('V01Host')) {
    if ($env:FT_V01_HOST) { $V01Host = $env:FT_V01_HOST }
}
if ([string]::IsNullOrWhiteSpace($V01Host)) { $V01Host = "165.227.165.131" }

if (-not $PSBoundParameters.ContainsKey('V02Host')) {
    if ($env:FT_V02_HOST) { $V02Host = $env:FT_V02_HOST }
}
if ([string]::IsNullOrWhiteSpace($V02Host)) { $V02Host = "139.59.139.196" }

if (-not $PSBoundParameters.ContainsKey('User')) {
    if ($env:FT_SSH_USER) { $User = $env:FT_SSH_USER }
}
if ([string]::IsNullOrWhiteSpace($User)) { $User = "root" }

if (-not $PSBoundParameters.ContainsKey('RepoRoot')) {
    if ($env:FT_REPO_ROOT) { $RepoRoot = $env:FT_REPO_ROOT }
}
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = "/root/freqtrade-coint-pairs-trading" }

$scriptPath = Join-Path $here "droplet_status_remote.sh"

if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Missing script: $scriptPath"
}

function BashSingleQuote([string]$s) {
    return "'" + ($s -replace "'", "'\''") + "'"
}

$scriptBody = (Get-Content -LiteralPath $scriptPath -Raw) -replace "`r`n", "`n" -replace "`r", "`n"

function Invoke-RemoteStatus([string]$Label, [string]$HostName) {
    $exports = @(
        "export FT_REPO_ROOT=$(BashSingleQuote $RepoRoot)",
        "export FT_LOG_TAIL=$LogTail"
    )
    if ($SkipTrades) {
        $exports += "export FT_SKIP_TRADES=1"
    }
    $remoteCmd = ($exports -join "; ") + "; bash -s"
    Write-Host ""
    Write-Host "################################################################################" -ForegroundColor Cyan
    Write-Host " $Label  ($User@$HostName)" -ForegroundColor Cyan
    Write-Host "################################################################################" -ForegroundColor Cyan
    $scriptBody | ssh -T "${User}@${HostName}" "$remoteCmd"
}

Invoke-RemoteStatus "DROPLET V01 (ports 8080-8082 on $V01Host)" $V01Host
Invoke-RemoteStatus "DROPLET V02 (ports 8083-8085 on $V02Host)" $V02Host

if (-not $SkipTrades) {
    $combinedPy = Join-Path $here "droplet_combined_summary_from_local.py"
    if (Test-Path -LiteralPath $combinedPy) {
        Write-Host ""
        try {
            & python $combinedPy --user $User --v01 $V01Host --v02 $V02Host
        } catch {
            Write-Host "Combined instance summary failed: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Missing: $combinedPy" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "All done." -ForegroundColor Green
