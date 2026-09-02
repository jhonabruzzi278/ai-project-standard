param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$HermesArgs
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
python -m hermes --config (Join-Path $repoRoot "hermes.config.json") @HermesArgs
exit $LASTEXITCODE
