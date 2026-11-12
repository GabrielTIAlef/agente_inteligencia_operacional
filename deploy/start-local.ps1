$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$nodeInstallRoot = Join-Path $env:LOCALAPPDATA 'Author Software\nvm\installs'
$nodeDirectory = Get-ChildItem -LiteralPath $nodeInstallRoot -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'node.exe') } |
    Sort-Object { [version]($_.Name -replace '^v','') } -Descending |
    Select-Object -First 1
if (-not $nodeDirectory) { throw 'Node não encontrado nas instalações do NVM.' }
$nodePath = Join-Path $nodeDirectory.FullName 'node.exe'
$env:PATH = "$($nodeDirectory.FullName);$env:PATH"
$env:N8N_LISTEN_ADDRESS = '127.0.0.1'
$env:N8N_DIAGNOSTICS_ENABLED = 'false'
$env:N8N_PERSONALIZATION_ENABLED = 'false'
$env:GENERIC_TIMEZONE = 'America/Sao_Paulo'

function Start-LocalService($serviceName, $port, $executable, $serviceArguments, $directory) {
    $listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host "$serviceName já possui processo na porta $port; nenhum processo foi substituído."
        return
    }
    Start-Process -FilePath $executable -ArgumentList $serviceArguments -WorkingDirectory $directory `
        -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot "local-$serviceName.log") `
        -RedirectStandardError (Join-Path $projectRoot "local-$serviceName-error.log")
    Write-Host "$serviceName iniciando em 127.0.0.1:$port. Consulte local-$serviceName*.log."
}

Start-LocalService 'api' 8000 $pythonPath '-m deploy.start-api' $projectRoot
Start-LocalService 'frontend' 5173 $nodePath 'node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort' (Join-Path $projectRoot 'frontend')
$n8nEntry = Join-Path $nodeDirectory.FullName 'node_modules\n8n\bin\n8n'
Start-LocalService 'n8n' 5678 $nodePath ('"' + $n8nEntry + '" start') $projectRoot
Write-Host 'Painel: http://127.0.0.1:5173 | n8n: http://127.0.0.1:5678'
Write-Host 'A agenda não é ativada por este script. O n8n pode levar alguns minutos neste PC.'
