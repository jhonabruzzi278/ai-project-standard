[CmdletBinding()]
param(
    [ValidateSet('abrir', 'estado', 'actualizar')]
    [string]$Accion = 'abrir'
)

$ErrorActionPreference = 'Stop'

$ssh = Get-Command ssh -ErrorAction Stop
$identity = Join-Path $env:USERPROFILE '.ssh\id_ed25519_logify_vps'
if (-not (Test-Path -LiteralPath $identity -PathType Leaf)) {
    throw "No se encontró la llave SSH: $identity"
}

$sshArgs = @(
    '-o', 'IdentitiesOnly=yes',
    '-i', $identity,
    '-p', '12587',
    '-t',
    'hermesadmin@45.7.229.25'
)

$deploy = 'cd /opt/hermes/source/deploy/vps'
$compose = 'sudo docker compose --env-file .env.cloud -f compose-cloud.yaml'

$remoteCommand = switch ($Accion) {
    'abrir' {
        "$deploy && $compose exec hermes hermes --cli"
    }
    'estado' {
        "$deploy && $compose ps && $compose logs --tail=30 hermes"
    }
    'actualizar' {
        "cd /opt/hermes/source && git pull --ff-only && $deploy && sudo ./prepare-cloud.sh && $compose up -d && $compose ps"
    }
}

& $ssh.Source @sshArgs $remoteCommand
if ($LASTEXITCODE -ne 0) {
    throw "La acción '$Accion' terminó con código $LASTEXITCODE."
}
