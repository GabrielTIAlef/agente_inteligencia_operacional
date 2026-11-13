param(
    [string]$IdentityFile = "$env:USERPROFILE\Downloads\keyprivate.key",
    [string]$DestinationRoot = "$env:LOCALAPPDATA\InteligenciaOperacional",
    [string]$PythonExecutable = 'C:\Python315\python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) { throw 'Chave SSH local nao encontrada.' }
if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) { throw 'Python nao encontrado.' }
$root = [System.IO.Path]::GetFullPath($DestinationRoot)
New-Item -ItemType Directory -Force -Path $root | Out-Null
$account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$accountSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
& icacls.exe $root /inheritance:r /grant:r ('*{0}:(OI)(CI)F' -f $accountSid) '*S-1-5-18:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel proteger a pasta de backup.' }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'offsite-backup.py') -Destination (Join-Path $root 'offsite-backup.py') -Force
$config = @{
    ssh_executable = "$env:WINDIR\System32\OpenSSH\ssh.exe"
    identity_file = [System.IO.Path]::GetFullPath($IdentityFile)
    ssh_target = 'ubuntu@137.131.236.116'
    backup_directory = Join-Path $root 'backups'
} | ConvertTo-Json
[System.IO.File]::WriteAllText((Join-Path $root 'config.json'), $config, [System.Text.UTF8Encoding]::new($false))
$pythonWindowless = Join-Path (Split-Path $PythonExecutable) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonWindowless)) { throw 'pythonw.exe nao encontrado.' }
$action = New-ScheduledTaskAction -Execute $pythonWindowless -Argument ('"{0}"' -f (Join-Path $root 'offsite-backup.py')) -WorkingDirectory $root
$triggers = @(3,9,15,21) | ForEach-Object { New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($_).AddMinutes(30)) }
$triggers += New-ScheduledTaskTrigger -AtLogOn -User $account
$principal = New-ScheduledTaskPrincipal -UserId $account -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName 'InteligenciaOperacional-BackupExterno' -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Copia verificada do backup PostgreSQL da VM Oracle para este computador, sem servicos pagos.' -Force | Out-Null
Write-Output "Tarefa instalada. Destino: $root"
