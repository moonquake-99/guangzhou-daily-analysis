@echo off
chcp 65001 >nul
echo ========================================
echo   广州日报舆情系统 - 快速设置向导
echo ========================================
echo.

echo [步骤1] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python已安装
echo.

echo [步骤2] 安装依赖包...
pip install streamlit pandas numpy jieba snownlp matplotlib wordcloud requests beautifulsoup4
echo ✅ 依赖包安装完成
echo.

echo [步骤3] 测试本地应用...
echo 正在启动本地测试版本...
start http://localhost:8570
python demo_quick.py
echo.

echo ========================================
echo   下一步操作指南
echo ========================================
echo.
echo 1. 创建GitHub账号: https://github.com
echo 2. 创建新仓库（Public）
echo 3. 克隆仓库到本地
echo 4. 复制所有文件到仓库目录
echo 5. 推送到GitHub
echo 6. 部署到Streamlit Cloud
echo.
echo 详细步骤请查看: DEPLOYMENT_GUIDE.md
echo.
pause
