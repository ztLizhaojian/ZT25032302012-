@echo off
chcp 65001 >nul

echo =================================================
echo 企业财务账目录入与利润核算系统
chcp 65001 >nul
echo =================================================
echo.
echo 正在检查Python环境...

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python环境。请先安装Python 3.7或更高版本。
    pause
    exit /b 1
)

:: 检查pip是否可用
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到pip。请确保Python安装时已包含pip。
    pause
    exit /b 1
)

:: 检查并创建虚拟环境（可选）
if not exist "venv" (
    echo 未检测到虚拟环境，正在创建...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo 创建虚拟环境失败，将直接使用系统Python环境。
    ) else (
        echo 虚拟环境创建成功。
    )
)

:: 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 正在激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 安装依赖
if exist "requirements.txt" (
    echo 正在检查并安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 安装依赖时出现错误，但将尝试继续运行程序...
    )
)

:: 启动程序
echo.
echo 正在启动企业财务系统...
echo 程序运行日志将显示在这里...
echo =================================================
echo.
python main.py

:: 暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
echo =================================================
echo 程序运行出现错误，请查看以上日志信息。
echo =================================================
    pause
)
