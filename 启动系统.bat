@echo off
REM 设置为中文编码
chcp 936 >nul

echo =============================================
echo 企业财务账目录入与利润核算系统
echo =============================================
echo.
echo 正在检查Python环境...

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境。请先安装Python 3.7或更高版本。
    pause
    exit /b 1
)

REM 检查pip是否可用
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到pip。请确保Python安装时已包含pip。
    pause
    exit /b 1
)

REM 安装依赖
echo 正在检查并安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 安装依赖时出现错误，但将尝试继续运行程序...
)

REM 启动程序
echo.
echo 正在启动企业财务系统...
echo =============================================
echo.
python main.py

REM 暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
echo =============================================
echo 程序运行出现错误，请查看以上日志信息。
echo =============================================
    pause
)
