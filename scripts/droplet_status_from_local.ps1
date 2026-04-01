# SSH to both Droplets and run droplet_status_remote.sh for a single status summary.
#
# Usage (from repo root):
#   .\scripts\droplet_status_from_local.ps1
#   .\scripts\droplet_status_from_local.ps1 -V01Host 165.227.165.131 -V02Host 139.59.139.196
#   .\scripts\droplet_status_from_local.ps1 -SkipTrades        # faster: docker + logs only
#   .\scripts\droplet_status_from_local.ps1 -LogTail 25

param(
    [string] $V01Host = "165.227.165.131",
    [string] $V02Host = "139.59.139.196",
    [string] $User = "root",
    [string] $RepoRoot = "/root/freqtrade-coint-pairs-trading",
    [int] $LogTail = 18,
    [switch] $SkipTrades
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
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

Write-Host ""
Write-Host "All done." -ForegroundColor Green
