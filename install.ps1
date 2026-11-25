<#
.SYNOPSIS
    Install NX Mechanical Engineering Skills for Antigravity, Codex, or Claude Code on Windows.
.PARAMETER Target
    Target agent skill directory: antigravity | codex | claude | all (default: all)
.EXAMPLE
    .\install.ps1 -Target antigravity
    .\install.ps1 -Target codex
#>
param(
    [ValidateSet("antigravity", "codex", "claude", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$RepoSkills = Join-Path $PSScriptRoot "skills"
if (-not (Test-Path $RepoSkills)) {
    throw "Cannot find skills directory at: $RepoSkills"
}

$Targets = @()
if ($Target -eq "antigravity" -or $Target -eq "all") {
    $Targets += @{ Name = "Antigravity"; Path = (Join-Path $HOME ".gemini\config\skills") }
}
if ($Target -eq "codex" -or $Target -eq "all") {
    $Targets += @{ Name = "Codex"; Path = (Join-Path $HOME ".codex\skills") }
}
if ($Target -eq "claude" -or $Target -eq "all") {
    $Targets += @{ Name = "Claude Code"; Path = (Join-Path $HOME ".claude\skills") }
}

$SkillDirs = Get-ChildItem -Directory -Path $RepoSkills
foreach ($t in $Targets) {
    New-Item -ItemType Directory -Force -Path $t.Path | Out-Null
    foreach ($s in $SkillDirs) {
        $dst = Join-Path $t.Path $s.Name
        if (Test-Path $dst) {
            Remove-Item -Recurse -Force $dst
        }
        Copy-Item -Path $s.FullName -Destination $t.Path -Recurse -Force
    }
    Write-Host "[OK] Installed $($SkillDirs.Count) skills for $($t.Name) -> $($t.Path)" -ForegroundColor Green
}

Write-Host "`nDone! Restart or start a new conversation for the agent to load the new skills." -ForegroundColor Cyan
