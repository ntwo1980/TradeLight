$ProgramPath = "D:\君弘君智交易系统\bin.x64\XtItClient.exe"
$LogPath = "D:\data\trade\restart.log"
$ProcessName = "XtItClient"

# 确保日志目录存在
$LogDir = Split-Path -Path $LogPath -Parent
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $Message"
    Add-Content -Path $LogPath -Value $logEntry -Encoding UTF8
    Write-Host $logEntry
}

function Is-TargetProcessRunning {
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    foreach ($proc in $processes) {
        try {
            # 尝试获取进程的完整路径
            if ($proc.Path -and ($proc.Path -eq $ProgramPath)) {
                return $true
            }
        } catch {
            # 某些系统进程或权限不足时 Path 可能无法读取，跳过
            Write-Log "无法读取进程 $($proc.Id) 的路径: $_"
        }
    }
    return $false
}

Write-Log "自动重启脚本启动（轮询 + 路径验证模式）"

while ($true) {
    if (-not (Is-TargetProcessRunning)) {
        # 再次确认文件是否存在
        if (-not (Test-Path $ProgramPath)) {
            Write-Log "错误：程序文件不存在！路径: $ProgramPath"
            Start-Sleep -Seconds 30  # 避免频繁报错
            continue
        }

        Write-Log "目标程序未运行，正在启动: $ProgramPath"
        try {
            Start-Process -FilePath $ProgramPath -WorkingDirectory (Split-Path $ProgramPath)
            Write-Log "启动命令已发出"
        } catch {
            Write-Log "启动失败: $_"
        }
        Start-Sleep -Seconds 5
    }

    Start-Sleep -Seconds 10
}