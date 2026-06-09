"""
广州日报新闻爬虫 - 多版面版本
爬取2025年11月至2026年4月的新闻数据（包含多个版面）
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
import shutil
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spider.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 输出目录配置
BASE_OUTPUT_DIR = 'news_data'

# 版面配置：node_id 对应网页URL中的节点ID
SECTIONS_CONFIG = {
    'A1': {'node_id': 'node_1', 'name': '头版'},
    'A2': {'node_id': 'node_867', 'name': '跑出加速度 干出新业绩'},
    'A3': {'node_id': 'node_868', 'name': '科技广州新观察'},
    'A4': {'node_id': 'node_869', 'name': '评论'},
    'A5': {'node_id': 'node_870', 'name': '要闻'},
    'A6': {'node_id': 'node_871', 'name': '粤韵'},
    'A7': {'node_id': 'node_872', 'name': 'A7版'},
    'A8': {'node_id': 'node_873', 'name': '要闻'},
    'A9': {'node_id': 'node_874', 'name': '要闻'},
    'A10': {'node_id': 'node_875', 'name': '综合'},
    'A11': {'node_id': 'node_876', 'name': '健康周刊'},
    'A12': {'node_id': 'node_877', 'name': '科技周刊'},
}

# 要爬取的月份列表 (年份, 月份)
# 抓取2025年11月至2026年3月的数据
MONTHS_TO_CRAWL = [
    (2025, 11),
    (2025, 12),
    (2026, 1),
    (2026, 2),
    (2026, 3),
]


def generate_date_list(year, month):
    """生成指定年月的日期列表"""
    dates = []
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    current_date = start_date
    while current_date < end_date:
        dates.append(current_date.strftime('%Y-%m/%d'))
        current_date += timedelta(days=1)
    
    return dates


def fetch_page(url, max_retries=3):
    """获取网页内容，带重试机制"""
    for attempt in range(max_retries):
        try:
            logger.info(f"正在请求: {url}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                logger.info(f"请求成功: {url}")
                return response.text
            else:
                logger.warning(f"请求失败，状态码: {response.status_code}, URL: {url}")
                
        except Exception as e:
            logger.error(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return None


def parse_news_list_page(html, date_str):
    """解析新闻列表页面，提取文章链接和标题"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    articles = []
    
    # 查找所有新闻链接（通常在a标签中）
    # 根据网站结构，新闻链接通常是 content_*.htm 格式
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link['href']
        title = link.get_text(strip=True)
        
        # 只处理文章详情页链接（content_*.htm格式）
        if 'content_' in href and '.htm' in href:
            # 过滤掉无效链接
            if title and len(title) > 2:
                # 构建完整URL
                full_url = f"https://gzdaily.dayoo.com/pc/html/{date_str}/{href}"
                articles.append({
                    'title': title,
                    'link': href,
                    'full_url': full_url
                })
    
    # 去重（基于链接）
    seen_links = set()
    unique_articles = []
    for article in articles:
        if article['link'] not in seen_links:
            seen_links.add(article['link'])
            unique_articles.append(article)
    
    logger.info(f"从列表页找到 {len(unique_articles)} 篇文章")
    return unique_articles


def save_news_data(news_data, date_str, year, month, section_code=None):
    """保存新闻数据到JSON文件"""
    if not news_data:
        logger.warning(f"没有数据可保存: {date_str}")
        return False
    
    # 构建输出目录（按版面分目录）
    if section_code:
        output_dir = os.path.join(BASE_OUTPUT_DIR, f"{year}-{month:02d}", section_code)
    else:
        output_dir = os.path.join(BASE_OUTPUT_DIR, f"{year}-{month:02d}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建文件名
    filename = f"{date_str.replace('/', '-')}.json"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存: {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return False


def parse_article_detail(html, date_str):
    """解析文章详情页，提取完整内容"""
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'lxml')
    
    # 提取标题（通常在h1标签中）
    title_tag = soup.find('h1')
    if not title_tag:
        title_tag = soup.find('h2')
    
    title = title_tag.get_text(strip=True) if title_tag else ''
    
    # 提取正文内容 - 更精确的选择器
    content_parts = []
    
    # 方法1: 查找包含"本文字数"的段落，这通常是文章开始的地方
    article_start = None
    all_p_tags = soup.find_all('p')
    
    for i, p_tag in enumerate(all_p_tags):
        text = p_tag.get_text(strip=True)
        if '本文字数' in text or '新华社' in text or '广州日报讯' in text:
            article_start = i
            break
    
    # 从找到的起始位置开始提取正文
    if article_start is not None:
        for p_tag in all_p_tags[article_start:]:
            text = p_tag.get_text(strip=True)
            # 跳过导航相关的文本
            if text and len(text) > 10:
                # 排除明显的导航文本
                if not any(keyword in text for keyword in [
                    '返回网站', '版面概览', '系列报刊', '目录', '本版', 
                    '往期', '分享', '客户端', '首页', '放大', '缩小',
                    '上一版', '下一版', '下载', '第A', '版：'
                ]):
                    content_parts.append(text)
    else:
        # 如果没找到明确的起始标记，尝试其他方法
        # 查找所有p标签，过滤掉短文本和导航文本
        for p_tag in all_p_tags:
            text = p_tag.get_text(strip=True)
            if text and len(text) > 20:
                # 排除导航相关文本
                if not any(keyword in text for keyword in [
                    '返回网站', '版面概览', '系列报刊', '目录', '本版',
                    '往期', '分享', '客户端', '首页', '放大', '缩小',
                    '上一版', '下一版', '下载'
                ]):
                    # 排除只有版面信息的行
                    if not (text.startswith('第A') and '版：' in text):
                        content_parts.append(text)
    
    # 合并内容
    content = '\n\n'.join(content_parts)
    
    # 清理内容：去除多余的空格和换行
    import re
    content = re.sub(r'\s+', ' ', content)  # 将多个空格/换行替换为单个空格
    content = content.strip()
    
    # 如果内容太短，认为解析失败
    if not content or len(content) < 50:
        logger.warning(f"提取的内容过短: {len(content)} 字符")
        return None
    
    logger.info(f"成功提取正文: {len(content)} 字符")
    
    return {
        'title': title,
        'content': content
    }


def crawl_date_section(date_str, year, month, section_code, section_info):
    """爬取指定日期和版面的新闻"""
    node_id = section_info['node_id']
    section_name = section_info['name']
    list_url = f"https://gzdaily.dayoo.com/pc/html/{date_str}/{node_id}.htm?v=1"
    
    # 检查是否已经爬取过
    output_dir = os.path.join(BASE_OUTPUT_DIR, f"{year}-{month:02d}", section_code)
    filename = f"{date_str.replace('/', '-')}.json"
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        logger.info(f"  [{section_code}] 跳过已爬取: {date_str}")
        return True
    
    # 获取列表页
    list_html = fetch_page(list_url)
    if not list_html:
        logger.error(f"  [{section_code}] 无法获取列表页: {date_str}")
        return False
    
    # 解析列表页，获取文章链接
    article_links = parse_news_list_page(list_html, date_str)
    
    if not article_links:
        logger.warning(f"  [{section_code}] 未找到文章链接: {date_str}")
        return False
    
    logger.info(f"  [{section_code}] 开始爬取 {len(article_links)} 篇文章...")
    
    articles_data = []
    success_count = 0
    
    for i, article_info in enumerate(article_links, 1):
        logger.info(f"    [{i}/{len(article_links)}] {article_info['title'][:30]}...")
        
        # 获取文章详情页
        detail_html = fetch_page(article_info['full_url'])
        
        if detail_html:
            # 解析文章详情
            article_data = parse_article_detail(detail_html, date_str)
            
            if article_data:
                article_data['url'] = article_info['full_url']
                article_data['publish_date'] = date_str.replace('/', '-')
                article_data['section'] = section_code
                article_data['section_name'] = section_name
                articles_data.append(article_data)
                success_count += 1
                logger.info(f"      ✓ 成功")
            else:
                logger.warning(f"      ✗ 解析失败")
        else:
            logger.warning(f"      ✗ 请求失败")
        
        # 每次请求后等待2秒
        time.sleep(2)
    
    # 保存数据
    if articles_data:
        news_data = {
            'date': date_str.replace('/', '-'),
            'section': section_code,
            'section_name': section_name,
            'list_url': list_url,
            'total_articles': len(articles_data),
            'success_count': success_count,
            'articles': articles_data
        }
        save_news_data(news_data, date_str, year, month, section_code)
        logger.info(f"  [{section_code}] 成功: {success_count}/{len(article_links)} 篇文章")
        return True
    else:
        logger.warning(f"  [{section_code}] 未能解析出任何文章数据: {date_str}")
        return False


def backup_month_data(year, month):
    """备份指定月份的数据到backup目录"""
    source_dir = os.path.join(BASE_OUTPUT_DIR, f"{year}-{month:02d}")
    backup_base_dir = os.path.join(BASE_OUTPUT_DIR, 'backup')
    backup_dir = os.path.join(backup_base_dir, f"{year}-{month:02d}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if not os.path.exists(source_dir):
        logger.warning(f"备份目录不存在: {source_dir}")
        return False
    
    try:
        os.makedirs(backup_base_dir, exist_ok=True)
        shutil.copytree(source_dir, backup_dir)
        logger.info(f"✓ 数据已备份到: {backup_dir}")
        
        # 统计备份的文件数量
        total_files = 0
        for root, dirs, files in os.walk(backup_dir):
            total_files += len([f for f in files if f.endswith('.json')])
        
        logger.info(f"  备份文件总数: {total_files} 个JSON文件")
        return True
    except Exception as e:
        logger.error(f"备份失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始爬取广州日报新闻数据（多版面版本）")
    logger.info(f"目标月份: {len(MONTHS_TO_CRAWL)} 个月")
    for year, month in MONTHS_TO_CRAWL:
        logger.info(f"  - {year}年{month}月")
    logger.info(f"目标版面: {len(SECTIONS_CONFIG)} 个版面")
    for code, info in SECTIONS_CONFIG.items():
        logger.info(f"  - {code}: {info['name']}")
    logger.info("=" * 60)
    
    total_success_days = 0
    total_fail_days = 0
    total_sections_crawled = 0
    
    # 持续运行直到所有月份完成
    while True:
        all_completed = True
        
        for year, month in MONTHS_TO_CRAWL:
            logger.info("\n" + "=" * 60)
            logger.info(f"开始处理: {year}年{month}月")
            logger.info("=" * 60)
            
            # 生成日期列表
            dates = generate_date_list(year, month)
            logger.info(f"总共需要爬取 {len(dates)} 天的数据")
            logger.info(f"每个日期需要爬取 {len(SECTIONS_CONFIG)} 个版面")
            logger.info(f"预计总请求数: {len(dates) * len(SECTIONS_CONFIG)} 次")
            
            success_count = 0
            fail_count = 0
            month_has_uncompleted = False
            
            for i, date_str in enumerate(dates, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"日期进度: [{i}/{len(dates)}] 处理日期: {date_str}")
                logger.info(f"{'='*60}")
                
                date_success = 0
                date_fail = 0
                
                # 遍历所有版面
                for section_idx, (section_code, section_info) in enumerate(SECTIONS_CONFIG.items(), 1):
                    logger.info(f"\n版面进度: [{section_idx}/{len(SECTIONS_CONFIG)}] {section_code} - {section_info['name']}")
                    
                    if crawl_date_section(date_str, year, month, section_code, section_info):
                        date_success += 1
                        total_sections_crawled += 1
                    else:
                        date_fail += 1
                        month_has_uncompleted = True
                    
                    # 版面之间等待2秒
                    if section_idx < len(SECTIONS_CONFIG):
                        time.sleep(2)
                
                if date_fail == 0:
                    success_count += 1
                else:
                    fail_count += 1
                
                logger.info(f"\n日期 {date_str} 完成: 成功{date_success}个版面, 失败{date_fail}个版面")
                
                # 日期之间等待2秒
                if i < len(dates):
                    time.sleep(2)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"{year}年{month}月 完成!")
            logger.info(f"  完全成功: {success_count} 天")
            logger.info(f"  部分失败: {fail_count} 天")
            logger.info(f"{'='*60}")
            
            # 备份该月数据
            logger.info(f"\n正在备份 {year}年{month}月 数据...")
            backup_month_data(year, month)
            
            total_success_days += success_count
            total_fail_days += fail_count
            
            if month_has_uncompleted:
                all_completed = False
        
        logger.info("\n" + "=" * 60)
        logger.info(f"本轮爬取完成!")
        logger.info(f"总成功天数: {total_success_days} 天")
        logger.info(f"总失败天数: {total_fail_days} 天")
        logger.info(f"总版面爬取数: {total_sections_crawled} 个版面")
        logger.info(f"数据保存在: {BASE_OUTPUT_DIR}")
        logger.info("=" * 60)
        
        # 如果所有月份都已完成，则退出循环
        if all_completed:
            logger.info("\n🎉 所有月份数据爬取完成！程序将退出。")
            break
        else:
            logger.info("\n🔄 检测到仍有未完成的数据，将继续爬取...")
            logger.info("等待10秒后开始下一轮爬取...")
            time.sleep(10)


if __name__ == '__main__':
    main()
