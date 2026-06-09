# 广州日报舆情分析系统 - 云端部署指南

## 📋 目录
1. [系统架构](#系统架构)
2. [前期准备](#前期准备)
3. [GitHub仓库设置](#github仓库设置)
4. [Streamlit Cloud部署](#streamlit-cloud部署)
5. [Windows定时任务配置](#windows定时任务配置)
6. [测试与验证](#测试与验证)
7. [常见问题](#常见问题)

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────┐
│          您的本地电脑                         │
│                                              │
│  ① 爬虫脚本 (crawl_gzdaily.py)               │
│     ↓ 每天凌晨2点执行                        │
│  ② 数据清洗 (data_cleaning.py)               │
│     ↓                                        │
│  ③ 情感分析 (自动在app中计算)                 │
│     ↓                                        │
│  ④ 生成 news_with_keywords.csv               │
│     ↓                                        │
│  ⑤ Git推送至GitHub                           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          GitHub仓库                          │
│                                              │
│  存储: news_with_keywords.csv                │
│        monthly_hot_topics.csv                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│       Streamlit Cloud (免费托管)              │
│                                              │
│  从GitHub读取CSV文件                         │
│  实时展示给所有用户                          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          任何用户的浏览器                     │
│                                              │
│  访问: https://your-app.streamlit.app        │
└─────────────────────────────────────────────┘
```

---

## 🛠️ 前期准备

### 1. 安装必要软件

```bash
# Python环境（已安装）
python --version

# 安装依赖包
pip install streamlit pandas numpy jieba snownlp matplotlib wordcloud requests beautifulsoup4
```

### 2. 创建GitHub账号

- 访问 https://github.com
- 注册免费账号
- 记住用户名和密码

### 3. 安装Git

- 下载: https://git-scm.com/download/win
- 安装后配置:
```bash
git config --global user.name "YourName"
git config --global user.email "youremail@example.com"
```

---

## 📦 GitHub仓库设置

### 步骤1: 创建新仓库

1. 登录GitHub
2. 点击右上角 "+" → "New repository"
3. 填写信息:
   - Repository name: `gzdaily-sentiment-analysis`
   - Description: `广州日报舆情分析系统`
   - **Public** (必须公开，Streamlit Cloud才能访问)
   - ✅ Add a README file
4. 点击 "Create repository"

### 步骤2: 克隆仓库到本地

```bash
cd C:\Users\17431\Desktop\python
git clone https://github.com/你的用户名/gzdaily-sentiment-analysis.git
cd gzdaily-sentiment-analysis
```

### 步骤3: 复制必要文件

将以下文件复制到仓库目录：
- `app_cloud.py` (云端版应用)
- `crawl_gzdaily.py` (爬虫脚本)
- `auto_update.py` (自动更新脚本)
- `data_cleaning.py` (数据清洗)
- `extract_hot_topics or word cloud.py` (热点提取)
- `stopwords.txt` (停用词)
- `news_with_keywords.csv` (现有数据)
- `monthly_hot_topics.csv` (热点关键词)

### 步骤4: 创建requirements.txt

```txt
streamlit==1.31.0
pandas==2.1.4
numpy==1.26.2
jieba==0.42.1
snownlp==0.12.3
matplotlib==3.8.2
wordcloud==1.9.3
requests==2.31.0
beautifulsoup4==4.12.2
```

### 步骤5: 提交并推送

```bash
git add .
git commit -m "Initial commit: 广州日报舆情分析系统"
git push origin main
```

---

## ☁️ Streamlit Cloud部署

### 步骤1: 访问Streamlit Cloud

- 网址: https://streamlit.io/cloud
- 点击 "Sign up with GitHub"
- 授权访问您的GitHub账号

### 步骤2: 创建新应用

1. 点击 "New app"
2. 选择您的仓库: `gzdaily-sentiment-analysis`
3. 填写配置:
   - **Branch**: `main`
   - **Main file path**: `app_cloud.py`
   - **App URL**: `gzdaily-sentiment` (自定义)
4. 点击 "Deploy!"

### 步骤3: 等待部署完成

- 首次部署需要3-5分钟
- 成功后会显示: `https://gzdaily-sentiment.streamlit.app`
- 这个URL可以分享给任何人访问！

### 步骤4: 修改app_cloud.py中的GitHub URL

在 `app_cloud.py` 中找到这一行：

```python
GITHUB_RAW_URL = "https://raw.githubusercontent.com/your-username/your-repo/main/news_with_keywords.csv"
```

替换为您的实际URL：

```python
GITHUB_RAW_URL = "https://raw.githubusercontent.com/你的用户名/gzdaily-sentiment-analysis/main/news_with_keywords.csv"
```

然后重新提交：

```bash
git add app_cloud.py
git commit -m "Update GitHub raw URL"
git push origin main
```

Streamlit Cloud会自动检测更新并重新部署（约1分钟）。

---

## ⏰ Windows定时任务配置

### 方法1: 使用任务计划程序（推荐）

#### 步骤1: 创建批处理文件 `run_update.bat`

```batch
@echo off
cd /d C:\Users\17431\Desktop\python\gzdaily-sentiment-analysis

echo ========================================
echo 开始自动更新流程
echo 时间: %date% %time%
echo ========================================

REM 运行自动更新脚本
python auto_update.py

REM 如果成功，推送到GitHub
if %errorlevel% equ 0 (
    echo.
    echo 正在推送到GitHub...
    git add .
    git commit -m "Auto update: %date% %time%"
    git push origin main
    echo ✅ 推送成功！
) else (
    echo ❌ 更新失败，请检查日志
)

echo.
echo 完成时间: %date% %time%
pause
```

#### 步骤2: 打开任务计划程序

1. 按 `Win + R`，输入 `taskschd.msc`
2. 点击右侧 "创建基本任务"

#### 步骤3: 配置任务

- **名称**: `GZDaily Auto Update`
- **描述**: `每天凌晨2点自动更新广州日报舆情数据`
- **触发器**: 
  - 选择 "每天"
  - 开始时间: `02:00:00`
  - 每隔: `1` 天
- **操作**:
  - 选择 "启动程序"
  - 程序/脚本: `C:\Users\17431\Desktop\python\gzdaily-sentiment-analysis\run_update.bat`
  - 起始于: `C:\Users\17431\Desktop\python\gzdaily-sentiment-analysis`
- **完成**: 点击 "完成"

#### 步骤4: 测试任务

1. 在任务列表中找到刚创建的任务
2. 右键 → "运行"
3. 观察是否成功执行

### 方法2: 使用Python的schedule库（备选）

创建 `scheduler.py`:

```python
import schedule
import time
import subprocess
from datetime import datetime

def job():
    print(f"[{datetime.now()}] 开始执行自动更新...")
    result = subprocess.run(['python', 'auto_update.py'])
    
    if result.returncode == 0:
        # 推送到GitHub
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', f'Auto update: {datetime.now()}'])
        subprocess.run(['git', 'push', 'origin', 'main'])
        print("✅ 更新并推送成功")
    else:
        print("❌ 更新失败")

# 每天凌晨2点执行
schedule.every().day.at("02:00").do(job)

print("⏰ 调度器已启动，等待执行...")

while True:
    schedule.run_pending()
    time.sleep(60)  # 每分钟检查一次
```

运行：

```bash
python scheduler.py
```

**注意**: 这种方法需要保持电脑开机且程序一直运行。

---

## ✅ 测试与验证

### 测试1: 手动运行爬虫

```bash
python crawl_gzdaily.py
```

预期输出：
```
============================================================
🚀 广州日报新闻爬虫启动
============================================================
📅 将爬取以下日期的新闻: ['2026-06-08', '2026-06-07', ...]
```

### 测试2: 手动运行完整流程

```bash
python auto_update.py
```

### 测试3: 推送到GitHub

```bash
git add .
git commit -m "Test update"
git push origin main
```

### 测试4: 访问Streamlit应用

1. 打开浏览器
2. 访问: `https://gzdaily-sentiment.streamlit.app`
3. 确认数据显示正常

### 测试5: 验证自动更新

1. 等待第二天凌晨2点
2. 检查GitHub仓库是否有新的commit
3. 访问Streamlit应用，确认数据已更新

---

## ❓ 常见问题

### Q1: Streamlit Cloud部署失败？

**A**: 检查以下几点：
1. 仓库是否是Public（必须公开）
2. requirements.txt是否正确
3. 查看部署日志（Deployments → View logs）

### Q2: 爬虫无法获取数据？

**A**: 可能原因：
1. 广州日报网站结构变化 → 需要调整爬虫代码
2. 反爬机制 → 添加延时、更换User-Agent
3. 网络问题 → 检查网络连接

### Q3: 情感分析太慢？

**A**: 优化方案：
1. 减少每次爬取的新闻数量
2. 使用缓存机制
3. 考虑使用更快的NLP库

### Q4: GitHub推送失败？

**A**: 解决方法：
```bash
# 配置Git凭据
git config --global credential.helper store

# 重新推送
git push origin main
```

### Q5: 如何更换域名？

**A**: Streamlit Cloud免费版不支持自定义域名。如需自定义域名，需要：
1. 购买服务器（阿里云/腾讯云）
2. 部署Streamlit应用
3. 配置Nginx反向代理
4. 绑定域名

---

## 📞 技术支持

如遇到问题，请检查：
1. Python版本: `python --version` (建议3.8+)
2. 依赖包版本: `pip list`
3. Git配置: `git config --list`
4. 网络连接: `ping github.com`

---

## 🎉 完成！

恭喜您成功部署了广州日报舆情分析系统！

现在您可以：
- ✅ 在任何电脑上访问应用
- ✅ 每天自动更新最新数据
- ✅ 实时监控舆情动态

**分享链接**: `https://gzdaily-sentiment.streamlit.app`

祝您使用愉快！🚀
