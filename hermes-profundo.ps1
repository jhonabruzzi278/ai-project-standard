param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$HermesArgs
)

[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
python -X utf8 -m hermes_deep --config (Join-Path $repoRoot "hermes.config.json") @HermesArgs
exit $LASTEXITCODE
