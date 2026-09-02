[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$skillsPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'skills')).Path

$hermesCommand = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermesCommand) {
    Write-Error "Hermes Agent CLI is not installed yet. Run 'ollama launch hermes' once and complete its setup, then run this script again."
}

Write-Host "Registering external Hermes skills: $skillsPath"
& $hermesCommand.Source config set skills.external_dirs "[$skillsPath]"
if ($LASTEXITCODE -ne 0) {
    throw "Hermes Agent rejected the external skills configuration."
}

Write-Host 'Validating discovered skills...'
& $hermesCommand.Source skills list
if ($LASTEXITCODE -ne 0) {
    throw "Hermes Agent could not list its skills."
}

Write-Host 'Hermes Agent integration is ready.'
Write-Host "Start it from $PSScriptRoot with: ollama launch hermes"
