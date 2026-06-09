"""
从JSON文件中提取新闻数据并合并成CSV
遍历所有月份文件夹和版面子文件夹，读取JSON文件，提取文章信息
"""

import json
import pandas as pd
import os
from pathlib import Path


def extract_articles_from_json(json_file):
    """
    从单个JSON文件中提取文章列表
    返回: list of dict, 每个dict包含 title, content, date
    """
    articles = []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否有articles字段
        if 'articles' not in data:
            print(f"  ⚠ 警告: {json_file} 中没有articles字段")
            return articles
        
        # 提取每篇文章
        for article in data['articles']:
            if 'title' in article and 'content' in article:
                # 优先使用publish_date，如果没有则使用文件名中的日期
                date = article.get('publish_date', '')
                
                # 如果publish_date为空，尝试从date字段获取
                if not date and 'date' in data:
                    date = data['date']
                
                # 如果还是没有，从文件名提取日期
                if not date:
                    # 文件名格式: 2025-11-01.json
                    filename = os.path.basename(json_file)
                    date = filename.replace('.json', '')
                
                # 提取URL
                url = article.get('url', '')
                
                articles.append({
                    'url': url,
                    'title': article['title'],
                    'content': article['content'],
                    'date': date
                })
    
    except Exception as e:
        print(f"  ❌ 错误: 读取 {json_file} 失败 - {e}")
    
    return articles


def collect_all_news(base_dir):
    """
    遍历所有月份文件夹和版面子文件夹，收集所有新闻
    参数:
        base_dir: 基础目录路径
    返回:
        DataFrame 包含所有新闻
    """
    all_articles = []
    file_count = 0
    
    # 获取所有月份文件夹（如 2025-11, 2025-12, 2026-01 等）
    month_folders = sorted([f for f in os.listdir(base_dir) 
                           if os.path.isdir(os.path.join(base_dir, f))])
    
    print(f"找到 {len(month_folders)} 个月份文件夹")
    
    for month_folder in month_folders:
        month_path = os.path.join(base_dir, month_folder)
        print(f"\n处理月份: {month_folder}")
        
        # 获取所有版面子文件夹（如 A1, A2, ..., A12）
        section_folders = sorted([f for f in os.listdir(month_path) 
                                 if os.path.isdir(os.path.join(month_path, f))])
        
        print(f"  找到 {len(section_folders)} 个版面")
        
        for section_folder in section_folders:
            section_path = os.path.join(month_path, section_folder)
            
            # 获取所有JSON文件
            json_files = [f for f in os.listdir(section_path) 
                         if f.endswith('.json')]
            
            for json_file in json_files:
                json_path = os.path.join(section_path, json_file)
                articles = extract_articles_from_json(json_path)
                all_articles.extend(articles)
                file_count += 1
                
                # 每处理100个文件显示一次进度
                if file_count % 100 == 0:
                    print(f"  已处理 {file_count} 个文件，累计 {len(all_articles)} 篇文章")
    
    print(f"\n✓ 总共处理了 {file_count} 个JSON文件")
    print(f"✓ 总共提取了 {len(all_articles)} 篇文章")
    
    # 转换为DataFrame
    df = pd.DataFrame(all_articles)
    
    return df


def main():
    """
    主函数：提取所有新闻并保存为CSV
    """
    print("="*60)
    print("广州日报新闻数据提取工具")
    print("="*60)
    
    # 设置基础目录
    base_dir = r"c:\Users\17431\Desktop\python"
    
    print(f"\n【步骤1】扫描目录: {base_dir}")
    
    # 收集所有新闻
    df = collect_all_news(base_dir)
    
    if len(df) == 0:
        print("\n❌ 错误: 没有提取到任何新闻数据")
        return
    
    # 显示数据统计
    print(f"\n【步骤2】数据统计")
    print(f"  总文章数: {len(df)}")
    print(f"  列名: {list(df.columns)}")
    
    # 检查空值
    null_counts = df.isnull().sum()
    print(f"\n  空值统计:")
    for col, count in null_counts.items():
        if count > 0:
            print(f"    {col}: {count} 条空值")
    
    # 显示日期范围
    if 'date' in df.columns:
        valid_dates = df['date'].dropna()
        if len(valid_dates) > 0:
            print(f"\n  日期范围: {valid_dates.min()} 至 {valid_dates.max()}")
    
    # 显示前几条数据示例
    print(f"\n  数据示例（前3条）:")
    print(df.head(3).to_string(index=False))
    
    # 保存为CSV
    output_file = os.path.join(base_dir, 'news.csv')
    print(f"\n【步骤3】保存数据到: {output_file}")
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✓ 成功保存 {len(df)} 条新闻记录")
    print(f"✓ 文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
    
    print("\n" + "="*60)
    print("数据提取完成！")
    print("="*60)
    print(f"\n下一步: 运行 python data_cleaning.py 进行数据清洗和分词")


if __name__ == '__main__':
    main()
