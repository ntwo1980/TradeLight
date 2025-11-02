@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 获取当前日期（格式：YYYYMMDD）
for /f "tokens=1-3 delims=/-" %%a in ('wmic os get localdatetime ^| findstr [0-9]') do (
    set datetime=%%a
)
set year=!datetime:~0,4!
set month=!datetime:~4,2!
set day=!datetime:~6,2!
set today=!year!!month!!day!

:: 获取星期几（0=周日, 1=周一, ..., 6=周六）
for /f "skip=1" %%a in ('wmic path win32_localtime get dayofweek') do (
    if not "%%a"=="" set dow=%%a & goto :got_dow
)
:got_dow

:: 如果是周六(6)或周日(0)，退出程序
if "!dow!"=="6" (
    echo 今天是周六，程序退出。
    exit /b
)
if "!dow!"=="0" (
    echo 今天是周日，程序退出。
    exit /b
)

:: 设置源目录和目标目录
set "source_dir=D:\君弘君智交易系统\bin.x64"
set "target_dir=D:\data\trade\%today%"

:: 创建目标目录
if not exist "%target_dir%" (
    mkdir "%target_dir%"
    echo 已创建目录: %target_dir%
)

:: 拷贝.json和.py文件
copy "%source_dir%\*.json" "%target_dir%" >nul 2>nul && echo 已拷贝.json文件到 %target_dir% || echo 源目录中没有.json文件
copy "%source_dir%\*.py" "%target_dir%" >nul 2>nul && echo 已拷贝.py文件到 %target_dir% || echo 源目录中没有.py文件

echo 操作完成！
pause