"""
广州日报新闻爬虫 - 自动更新版
每天凌晨2点自动爬取最新新闻
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import time
import re

# ==================== 配置 ====================
BASE_URL = "https://newspaper.gzdaily.cn"
OUTPUT_DIR = "raw_news_data"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def ensure_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def get_date_list(days_back=7):
    """
    获取需要爬取的日期列表
    默认爬取最近7天的新闻
    """
    dates = []
    for i in range(days_back):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    return dates

def crawl_news_list(date_str):
    """
    爬取指定日期的新闻列表
    
    注意：由于广州日报数字报的网站结构可能比较复杂，
    这里提供一个通用框架，实际使用时需要根据网站结构调整
    
    Args:
        date_str: 日期字符串，格式 'YYYY-MM-DD'
    
    Returns:
        新闻URL列表
    """
    print(f"📅 正在爬取 {date_str} 的新闻列表...")
    
    # TODO: 根据实际网站结构调整URL格式
    # 示例URL格式（需要根据实际情况修改）
    url = f"{BASE_URL}/html/{date_str.replace('-', '/')}/node_1.htm"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"⚠️ {date_str} 页面返回状态码: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: 根据实际HTML结构调整选择器
        # 示例：查找所有新闻链接
        news_links = []
        
        # 这里需要根据实际网页结构调整
        # 例如：soup.find_all('a', class_='news-link')
        
        print(f"✅ {date_str} 找到 {len(news_links)} 条新闻")
        return news_links
        
    except Exception as e:
        print(f"❌ 爬取 {date_str} 失败: {e}")
        return []

def crawl_news_detail(url):
    """
    爬取单篇新闻详情
    
    Args:
        url: 新闻URL
    
    Returns:
        新闻字典 {'title': '', 'content': '', 'date': '', 'reporter': ''}
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: 根据实际HTML结构调整选择器
        title = ""  # soup.find('h1').get_text().strip()
        content = ""  # soup.find('div', class_='content').get_text().strip()
        date = ""  # soup.find('span', class_='date').get_text().strip()
        
        # 提取记者信息
        reporter = ""
        reporter_match = re.search(r'[（(]记者([^）)]+)[）)]', content)
        if reporter_match:
            reporter = reporter_match.group(1).strip()
        
        return {
            'title': title,
            'content': content,
            'date': date,
            'reporter': reporter,
            'url': url
        }
        
    except Exception as e:
        print(f"❌ 爬取新闻详情失败: {e}")
        return None

def save_to_json(news_list, date_str):
    """
    保存新闻数据为JSON格式
    
    Args:
        news_list: 新闻列表
        date_str: 日期字符串
    """
    ensure_dir()
    
    filename = os.path.join(OUTPUT_DIR, f"{date_str}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)
    
    print(f"💾 已保存 {len(news_list)} 条新闻到 {filename}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 广州日报新闻爬虫启动")
    print("=" * 60)
    
    # 获取需要爬取的日期
    dates = get_date_list(days_back=7)
    print(f"📅 将爬取以下日期的新闻: {dates}")
    
    all_news = []
    
    for date_str in dates:
        print(f"\n{'='*60}")
        print(f"处理日期: {date_str}")
        print(f"{'='*60}")
        
        # 爬取新闻列表
        news_urls = crawl_news_list(date_str)
        
        if not news_urls:
            print(f"⚠️ {date_str} 没有新闻或爬取失败，跳过")
            continue
        
        # 爬取每篇新闻详情
        daily_news = []
        for url in news_urls:
            news = crawl_news_detail(url)
            if news:
                daily_news.append(news)
                time.sleep(1)  # 避免请求过快
        
        # 保存当天新闻
        if daily_news:
            save_to_json(daily_news, date_str)
            all_news.extend(daily_news)
        
        # 每天之间等待2秒
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"✅ 爬取完成！共获取 {len(all_news)} 条新闻")
    print(f"{'='*60}")
    
    return all_news

if __name__ == "__main__":
    main()
