@echo off
chcp 65001 >nul
echo ========================================
echo   广州日报舆情分析系统 - 启动脚本
echo ========================================
echo.

echo [1/3] 检查依赖库...
python -c "import streamlit, pandas, matplotlib, wordcloud, jieba, snownlp" 2>nul
if errorlevel 1 (
    echo ❌ 缺少依赖库，正在安装...
    pip install streamlit pandas matplotlib wordcloud jieba snownlp requests beautifulsoup4 numpy pillow
) else (
    echo ✅ 所有依赖库已安装
)

echo.
echo [2/3] 启动 Streamlit 应用...
echo.
echo 💡 提示：浏览器会自动打开 http://localhost:8501
echo.

streamlit run app.py

pause
