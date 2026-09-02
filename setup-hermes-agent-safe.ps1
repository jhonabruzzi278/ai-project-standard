[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$skillsPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'skills')).Path
$hermesCommand = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermesCommand) {
    throw "Hermes Agent CLI is not installed. Run 'ollama launch hermes --config' first."
}

$hermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$configPath = Join-Path $hermesHome 'config.yaml'
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Hermes Agent config was not found at $configPath."
}

$escapedPath = $skillsPath.Replace("'", "''")
$lines = [System.Collections.Generic.List[string]](Get-Content -LiteralPath $configPath)
$skillsStart = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^skills:\s*$') { $skillsStart = $i; break }
}

if ($skillsStart -lt 0) {
    $lines.Add('skills:')
    $lines.Add('  external_dirs:')
    $lines.Add("    - '$escapedPath'")
} else {
    $skillsEnd = $lines.Count
    for ($i = $skillsStart + 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\S') { $skillsEnd = $i; break }
    }

    $externalStart = -1
    for ($i = $skillsStart + 1; $i -lt $skillsEnd; $i++) {
        if ($lines[$i] -match '^  external_dirs:\s*$') { $externalStart = $i; break }
    }

    if ($externalStart -lt 0) {
        $lines.Insert($skillsEnd, '  external_dirs:')
        $lines.Insert($skillsEnd + 1, "    - '$escapedPath'")
    } else {
        $externalEnd = $skillsEnd
        for ($i = $externalStart + 1; $i -lt $skillsEnd; $i++) {
            if ($lines[$i] -match '^  \S' -and $lines[$i] -notmatch '^    ') { $externalEnd = $i; break }
        }
        $alreadyPresent = $false
        for ($i = $externalStart + 1; $i -lt $externalEnd; $i++) {
            if ($lines[$i].Trim().TrimStart('-').Trim().Trim("'") -eq $skillsPath) { $alreadyPresent = $true; break }
        }
        if (-not $alreadyPresent) {
            $lines.Insert($externalEnd, "    - '$escapedPath'")
        }
    }
}

$backupPath = "$configPath.hermes-aidlc.bak"
Copy-Item -LiteralPath $configPath -Destination $backupPath -Force
[System.IO.File]::WriteAllLines($configPath, $lines, [System.Text.UTF8Encoding]::new($false))

$env:HERMES_HOME = $hermesHome
$skillsOutput = (& $hermesCommand.Source skills list | Out-String)
if ($LASTEXITCODE -ne 0 -or $skillsOutput -notmatch 'hermes-aidlc-conductor') {
    throw "Hermes Agent did not discover hermes-aidlc-conductor. Restore $backupPath if needed."
}

Write-Host "Hermes Agent integration ready."
Write-Host "External skills: $skillsPath"
Write-Host "Config backup: $backupPath"
Write-Host "Launch from this folder with: ollama launch hermes --model qwen3:8b"
