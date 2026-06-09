"""
广州日报新闻数据清洗与分词脚本
功能：
1. 读取news.csv原始数据
2. 数据清洗（去空、日期格式化、按月分组）
3. 中文分词与停用词过滤
4. 输出清洗后的数据和统计信息
"""

import pandas as pd
import jieba
import re
import os
from datetime import datetime
from collections import Counter


def load_stopwords(stopwords_file='stopwords.txt'):
    """
    加载停用词表
    如果文件不存在，使用内置的常见停用词列表
    """
    default_stopwords = [
        '的', '了', '在', '是', '我', '也', '都', '就', '不', '有',
        '和', '与', '或', '等', '对', '进行', '并', '而', '这', '那',
        '他', '她', '它', '们', '你', '我们', '你们', '他们', '她们',
        '这个', '那个', '这些', '那些', '什么', '怎么', '为什么',
        '可以', '可能', '应该', '会', '要', '能', '不能', '不会',
        '已经', '正在', '曾经', '将要', '必须', '需要', '想要',
        '因为', '所以', '但是', '如果', '虽然', '然而', '因此',
        '从', '到', '向', '往', '于', '以', '为', '被', '把', '让',
        '着', '过', '得', '地', '很', '非常', '特别', '更加', '比较',
        '一个', '一些', '一种', '一下', '一样', '一起', '一直',
        '没有', '不是', '不要', '不要', '不用', '不必', '不敢',
        '自己', '别人', '大家', '人们', '朋友', '同学', '老师',
        '今天', '明天', '昨天', '现在', '以后', '以前', '当时',
        '这里', '那里', '哪里', '哪个', '哪些', '多少', '几',
        '说', '讲', '看', '听', '想', '做', '走', '来', '去',
        '好', '坏', '大', '小', '多', '少', '高', '低', '长', '短',
        '年', '月', '日', '时', '分', '秒', '星期', '号',
        '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '百', '千', '万', '亿', '第', '次', '回', '遍', '趟',
        '吗', '呢', '吧', '啊', '呀', '哦', '嗯', '唉', '哇',
        '之', '其', '此', '该', '某', '各', '每', '所有', '任何',
        '关于', '对于', '至于', '由于', '根据', '按照', '通过',
        '作为', '成为', '认为', '觉得', '知道', '了解', '发现',
        '表示', '显示', '说明', '指出', '提到', '报道', '据悉'
    ]
    
    if os.path.exists(stopwords_file):
        try:
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                stopwords = set([line.strip() for line in f if line.strip()])
            print(f"✓ 已从文件加载停用词: {len(stopwords)} 个")
            return stopwords
        except Exception as e:
            print(f"⚠ 读取停用词文件失败: {e}，使用默认停用词表")
            return set(default_stopwords)
    else:
        print(f"⚠ 停用词文件 '{stopwords_file}' 不存在，使用默认停用词表 ({len(default_stopwords)} 个)")
        print("提示: 你可以创建 stopwords.txt 文件，每行一个停用词")
        return set(default_stopwords)


def parse_date(date_str):
    """
    解析各种格式的日期字符串，统一转换为 YYYY-MM-DD 格式
    支持的格式包括:
    - "2025年11月5日"
    - "2025-11-05"
    - "2025/11/5"
    - "2025.11.05"
    - "20251105"
    等等
    """
    if pd.isna(date_str) or str(date_str).strip() == '':
        return None
    
    date_str = str(date_str).strip()
    
    # 尝试多种日期格式
    date_formats = [
        '%Y年%m月%d日',      # 2025年11月5日
        '%Y-%m-%d',          # 2025-11-05
        '%Y/%m/%d',          # 2025/11/5
        '%Y.%m.%d',          # 2025.11.05
        '%Y%m%d',            # 20251105
        '%Y年%m月%d号',      # 2025年11月5号
        '%Y-%m-%d %H:%M:%S', # 2025-11-05 10:30:00
        '%Y/%m/%d %H:%M:%S', # 2025/11/5 10:30:00
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # 如果以上格式都不匹配，尝试更灵活的正则表达式
    # 匹配类似 "2025年11月5日" 的格式（允许月份和日期没有前导零）
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})[日号]', date_str)
    if match:
        year, month, day = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # 匹配类似 "2025-11-5" 或 "2025/11/5" 的格式
    match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # 无法解析的日期
    return None


def clean_data(df):
    """
    数据清洗主函数
    1. 删除 url、title、content、date 中任意一个字段为空的行
    2. 日期格式化为 YYYY-MM-DD
    3. 新增 month 列（YYYY-MM 格式）
    4. 统计每月新闻数量
    """
    print("\n" + "="*60)
    print("开始数据清洗...")
    print("="*60)
    
    initial_count = len(df)
    print(f"原始数据量: {initial_count} 条")
    
    # 1. 去空：删除 url、title、content、date 中任意一个字段为空的行
    required_columns = ['title', 'content', 'date']
    if 'url' in df.columns:
        required_columns.insert(0, 'url')
    
    df_cleaned = df.dropna(subset=required_columns)
    after_dropna = len(df_cleaned)
    print(f"去除空值后: {after_dropna} 条 (删除了 {initial_count - after_dropna} 条)")
    
    # 2. 日期格式化
    print("\n正在解析日期格式...")
    df_cleaned['date_parsed'] = df_cleaned['date'].apply(parse_date)
    
    # 删除无法解析日期的行
    before_date_filter = len(df_cleaned)
    df_cleaned = df_cleaned.dropna(subset=['date_parsed'])
    after_date_filter = len(df_cleaned)
    print(f"日期解析后: {after_date_filter} 条 (删除了 {before_date_filter - after_date_filter} 条无效日期)")
    
    # 更新 date 列为格式化后的日期
    df_cleaned['date'] = df_cleaned['date_parsed']
    df_cleaned.drop(columns=['date_parsed'], inplace=True)
    
    # 3. 按月分组：新增 month 列（YYYY-MM 格式）
    df_cleaned['month'] = df_cleaned['date'].str[:7]  # 取前7个字符，即 YYYY-MM
    
    # 4. 统计每月新闻数量
    monthly_counts = df_cleaned.groupby('month').size().reset_index(name='count')
    monthly_counts = monthly_counts.sort_values('month').reset_index(drop=True)
    
    print(f"\n清洗完成！最终数据量: {len(df_cleaned)} 条")
    print(f"共覆盖 {len(monthly_counts)} 个月份")
    
    return df_cleaned, monthly_counts


def segment_text(text, stopwords):
    """
    对文本进行中文分词和停用词过滤
    参数:
        text: 待分词的文本
        stopwords: 停用词集合
    返回:
        分词后用空格连接的字符串
    """
    if pd.isna(text) or not isinstance(text, str):
        return ''
    
    # 使用 jieba 精确模式分词
    words = jieba.cut(text)
    
    # 过滤条件:
    # 1. 长度大于1
    # 2. 不在停用词表中
    # 3. 不是纯数字
    # 4. 不是纯标点符号
    filtered_words = []
    for word in words:
        word = word.strip()
        
        # 跳过空字符串
        if not word:
            continue
        
        # 跳过长度为1的词
        if len(word) <= 1:
            continue
        
        # 跳过停用词
        if word in stopwords:
            continue
        
        # 跳过纯数字
        if word.isdigit():
            continue
        
        # 跳过纯标点符号（只包含标点）
        if re.match(r'^[\W_]+$', word):
            continue
        
        filtered_words.append(word)
    
    # 用空格连接分词结果
    return ' '.join(filtered_words)





def main():
    """
    主函数：执行完整的数据清洗与分词流程
    """
    print("="*60)
    print("广州日报新闻数据清洗与分词系统")
    print("="*60)
    
    # ==================== 配置部分 ====================
    input_file = 'news.csv'              # 输入文件
    output_cleaned = 'news_cleaned.csv'  # 清洗后的数据
    output_monthly_counts = 'monthly_counts.csv'  # 每月统计
    stopwords_file = 'stopwords.txt'     # 停用词文件
    
    # ==================== 步骤1: 读取数据 ====================
    print("\n【步骤1】读取原始数据...")
    if not os.path.exists(input_file):
        print(f"❌ 错误: 找不到输入文件 '{input_file}'")
        print("请确保 news.csv 文件在当前目录下")
        return
    
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
        print(f"✓ 成功读取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
    except UnicodeDecodeError:
        # 如果 UTF-8 编码失败，尝试 GBK 编码（中文Windows常用）
        try:
            df = pd.read_csv(input_file, encoding='gbk')
            print(f"✓ 使用 GBK 编码成功读取 {len(df)} 条记录")
            print(f"  列名: {list(df.columns)}")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 检查必要的列是否存在
    required_columns = ['title', 'content', 'date']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ 错误: 缺少必要的列: {missing_columns}")
        print(f"当前列名: {list(df.columns)}")
        return
    
    # ==================== 步骤2: 加载停用词 ====================
    print("\n【步骤2】加载停用词表...")
    stopwords = load_stopwords(stopwords_file)
    
    # ==================== 步骤3: 数据清洗 ====================
    print("\n【步骤3】执行数据清洗...")
    df_cleaned, monthly_counts = clean_data(df)
    
    if len(df_cleaned) == 0:
        print("❌ 清洗后没有数据，程序退出")
        return
    
    # 打印清洗后的前3条记录示例
    print("\n清洗后的数据示例（前3条）:")
    print(df_cleaned[['title', 'date', 'month']].head(3).to_string(index=False))
    
    # 打印每月统计表前5行
    print("\n每月新闻数量统计（前5行）:")
    print(monthly_counts.head().to_string(index=False))
    
    # ==================== 步骤4: 中文分词 ====================
    print("\n【步骤4】执行中文分词与停用词过滤...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    # 初始化 jieba（可选：加载自定义词典）
    # jieba.load_userdict('user_dict.txt')  # 如果有自定义词典
    
    # 对 content 列进行分词
    df_cleaned['content_cut'] = df_cleaned['content'].apply(
        lambda x: segment_text(x, stopwords)
    )
    
    print(f"✓ 分词完成！处理了 {len(df_cleaned)} 条新闻")
    
    # 打印分词示例
    print("\n分词结果示例（第1条新闻的前50个词）:")
    first_cut = df_cleaned.iloc[0]['content_cut']
    words = first_cut.split()[:50]
    print(' '.join(words))
    if len(first_cut.split()) > 50:
        print(f"... (共 {len(first_cut.split())} 个词)")
    
    # ==================== 步骤5: 保存结果 ====================
    print("\n【步骤6】保存结果文件...")
    
    # 调整列顺序：url, title, content, date, month, content_cut
    desired_columns = ['url', 'title', 'content', 'date', 'month', 'content_cut']
    # 只保留存在的列
    existing_columns = [col for col in desired_columns if col in df_cleaned.columns]
    df_cleaned = df_cleaned[existing_columns]
    
    # 1. 保存清洗后的完整数据
    df_cleaned.to_csv(output_cleaned, index=False, encoding='utf-8-sig')
    print(f"✓ 已保存: {output_cleaned} ({len(df_cleaned)} 条记录)")
    
    # 2. 保存每月统计
    monthly_counts.to_csv(output_monthly_counts, index=False, encoding='utf-8-sig')
    print(f"✓ 已保存: {output_monthly_counts} ({len(monthly_counts)} 个月份)")
    
    # ==================== 总结 ====================
    print("\n" + "="*60)
    print("数据处理完成！")
    print("="*60)
    print(f"\n输出文件:")
    print(f"  1. {output_cleaned} - 清洗后的完整数据")
    print(f"  2. {output_monthly_counts} - 每月新闻数量统计")
    print(f"\n数据统计:")
    print(f"  - 总新闻数: {len(df_cleaned)}")
    print(f"  - 月份数: {len(monthly_counts)}")
    print(f"  - 时间范围: {monthly_counts['month'].min()} 至 {monthly_counts['month'].max()}")
    print(f"  - 平均每月新闻数: {monthly_counts['count'].mean():.1f}")
    
    # 显示每月的详细统计
    print(f"\n每月新闻数量详情:")
    for _, row in monthly_counts.iterrows():
        bar = '█' * int(row['count'] / 10)  # 简单的柱状图
        print(f"  {row['month']}: {row['count']:4d} 条 {bar}")


if __name__ == '__main__':
    main()
