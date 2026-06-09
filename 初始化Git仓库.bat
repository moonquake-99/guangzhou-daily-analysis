@echo off
chcp 65001 >nul
echo ========================================
echo   广州日报舆情分析系统 - Git初始化向导
echo ========================================
echo.

REM 检查是否已安装Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到Git,请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] 检查Git安装... OK
echo.

REM 检查是否已在Git仓库中
if exist .git (
    echo [提示] 当前目录已是Git仓库
    echo.
    choice /C YN /M "是否重新初始化?这将删除现有Git历史"
    if errorlevel 2 goto skip_init
    if errorlevel 1 (
        echo 正在删除现有Git仓库...
        rmdir /s /q .git
    )
)

:skip_init
echo [2/5] 初始化Git仓库...
git init
echo.

echo [3/5] 添加所有文件...
git add .
echo.

echo [4/5] 提交代码...
git commit -m "Initial commit: 广州日报舆情分析系统"
echo.

echo ========================================
echo   Git仓库初始化完成!
echo ========================================
echo.
echo 接下来请执行以下步骤:
echo.
echo 1. 在GitHub创建新仓库 (公开仓库)
echo    访问: https://github.com/new
echo.
echo 2. 复制您的仓库地址,然后运行:
echo    git remote add origin https://github.com/您的用户名/仓库名.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 详细步骤请查看: 云端部署指南.md
echo.
pause
