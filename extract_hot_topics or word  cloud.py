"""
每月热点话题提取脚本
从 news_cleaned.csv 中提取真正反映话题的名词性关键词，输出每月 Top 10

功能特点：
- 从标题（title）提取关键词，而非正文
- 严格过滤地域名称、媒体相关词、无意义动词/形容词等
- 支持自定义停用词文件（extra_stopwords.txt）
- 内置详细的过滤词列表
- 输出 CSV 文件和控制台展示
"""

import pandas as pd
import re
from collections import Counter
import os


# ==================== 停用词黑名单 ====================

# 1. 地域名称（包括省市、简称、别称等）
LOCATION_WORDS = {
    '广州', '广东', '广州市', '广东省', '粤', '羊城', '花城',
    '深圳', '深圳市', '珠海', '珠海市', '佛山', '佛山市',
    '东莞', '东莞市', '中山', '中山市', '惠州', '惠州市',
    '江门', '江门市', '肇庆', '肇庆市', '清远', '清远市',
    '汕头', '汕头市', '湛江', '湛江市', '茂名', '茂名市',
    '韶关', '韶关市', '河源', '河源市', '梅州', '梅州市',
    '汕尾', '汕尾市', '阳江', '阳江市', '云浮', '云浮市',
    '潮州', '潮州市', '揭阳', '揭阳市',
    '中国', '北京', '上海', '天津', '重庆',
    '香港', '澳门', '台湾',
}

# 2. 媒体/报社相关词汇
MEDIA_WORDS = {
    '记者', '本报', '编辑', '通讯员', '广州日报', '日报',
    '南方日报', '信息时报', '新快报', '羊城晚报', '南方都市报',
    '澎湃新闻', '新华社', '人民日报', '央视新闻', '凤凰卫视',
    '新浪网', '腾讯网', '网易', '搜狐', '今日头条',
    '公众号', '微信', '微博', '抖音', '快手',
    '报道', '采访', '新闻', '消息', '快讯', '直播',
    '主播', '主持人', '评论员', '特约', '专栏',
}

# 3. 领导人姓名（国家主席、总理等）
LEADER_NAMES = {
    '习近平', '李克强', '李强', '汪洋', '王沪宁',
    '赵乐际', '韩正', '丁薛祥', '陈希', '胡春华',
    '刘鹤', '孙春兰', '杨洁篪', '郭声琨', '黄坤明',
    '蔡奇', '王毅', '肖捷', '郑建邦', '何立峰',
    '王小洪', '吴政隆', '谌贻琴', '总书记', '总理', '主席'
}

# 4. 通用的无意义动词/形容词/抽象词
GENERIC_WORDS = {
    # 泛化动词
    '建设', '推动', '发展', '提高', '加强', '促进', '开展',
    '进行', '实现', '坚持', '努力', '推进', '落实', '做好',
    '完成', '实施', '执行', '组织', '安排', '部署',
    '要求', '强调', '指出', '提出', '表示', '认为', '说明',
    '介绍', '了解', '据悉', '通报', '发布', '公布',
    
    # 会议/活动通用词（太泛，没有区分度）
    '举行', '召开', '开幕', '闭幕', '启动', '举办',
    '参加', '出席', '莅临', '座谈', '调研', '考察',
    '会见', '接见', '慰问', '祝贺', '庆祝',
    
    # 公文常用词
    '关于', '贯彻', '学习', '精神', '公告', '通知',
    '决定', '意见', '方案', '规划', '计划', '总结',
    '报告', '讲话', '发言', '致辞', '指示',
    
    # 泛化形容词/副词
    '积极', '重要', '主要', '良好', '广大', '全面', '深入',
    '持续', '进一步', '不断', '加快', '大力', '认真',
    '切实', '有效', '显著', '突出', '明显', '稳步',
    
    # 泛指名词/代词
    '群众', '市民', '人们', '我们', '他们', '大家', '各位',
    '这个', '那个', '这些', '那些', '其中', '上述', '以下',
    '有关', '相关', '目前', '当前', '今后', '未来',
    
    # 其他高频但无信息量的词
    '工作', '产业', '城市', '服务', '企业', '单位', '部门',
    '项目', '活动', '会议', '情况', '问题', '方面', '领域',
    '水平', '能力', '质量', '效益', '成果', '经验', '做法',
    
    
    
    # 不完整的词（会被完整词替代）
    '全运',  # 应该用"全运会"
    '大湾',  # 应该用"大湾区"
    '十五',  # 应该用"十五运会"或"十五届"
}

# 5. 时间词
TIME_WORDS = {
    '今日', '昨日', '明天', '今天', '昨天', '日前', '此前',
    '现在', '未来', '过去', '年度', '月度', '上午', '下午',
    '时分', '时刻', '时候', '期间', '时期', '阶段',
    '今年', '去年', '明年', '当月', '本月', '上月',
    '近期', '远期', '长期', '短期', '暂时', '随时',
}

# 6. 合并所有内置停用词
BUILTIN_STOPWORDS = (
    LOCATION_WORDS | MEDIA_WORDS | LEADER_NAMES | 
    GENERIC_WORDS | TIME_WORDS
)


def load_extra_stopwords(filepath='extra_stopwords.txt'):
    """
    加载用户自定义的额外停用词文件
    如果文件不存在，返回空集合
    """
    extra_words = set()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:  # 跳过空行
                        extra_words.add(word)
            print(f"✓ 已加载自定义停用词: {len(extra_words)} 个")
        except Exception as e:
            print(f"⚠ 警告: 读取 {filepath} 失败 - {e}")
    else:
        print(f"ℹ 未找到 {filepath}，使用内置停用词表")
    
    return extra_words


def filter_word(word, all_stopwords):
    """
    判断一个词是否应该被过滤掉
    
    过滤规则：
    1. 长度 < 2 的词（单字词）
    2. 在停用词列表中
    3. 纯数字
    4. 纯标点符号
    
    参数:
        word: 待判断的词
        all_stopwords: 完整的停用词集合
    返回:
        True 表示应该过滤，False 表示保留
    """
    # 规则1: 长度 < 2
    if len(word) < 2:
        return True
    
    # 规则2: 在停用词列表中
    if word in all_stopwords:
        return True
    
    # 规则3: 纯数字
    if word.isdigit():
        return True
    
    # 规则4: 纯标点符号
    if re.match(r'^[\W_]+$', word):
        return True
    
    # 通过所有检查，保留该词
    return False


def extract_monthly_topics(input_file='news_cleaned.csv', 
                          output_file='monthly_hot_topics.csv',
                          top_n=10):
    """
    提取每月热点话题 Top N（从标题提取关键词）
    
    参数:
        input_file: 输入的清洗后数据文件
        output_file: 输出的热点话题文件
        top_n: 每个月返回的关键词数量
    """
    print("=" * 70)
    print("每月热点话题提取（从标题提取）")
    print("=" * 70)
    
    # ==================== 步骤1: 加载停用词 ====================
    print("\n【步骤1】加载停用词...")
    extra_stopwords = load_extra_stopwords('extra_stopwords.txt')
    all_stopwords = BUILTIN_STOPWORDS | extra_stopwords
    print(f"  内置停用词: {len(BUILTIN_STOPWORDS)} 个")
    print(f"  总停用词数: {len(all_stopwords)} 个")
    
    # ==================== 步骤2: 读取数据 ====================
    print(f"\n【步骤2】读取数据: {input_file}")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"  ✓ 成功读取 {len(df)} 条记录")
        print(f"  列名: {list(df.columns)}")
    except FileNotFoundError:
        print(f"  ❌ 错误: 找不到文件 {input_file}")
        return
    except Exception as e:
        print(f"  ❌ 错误: 读取文件失败 - {e}")
        return
    
    # 检查必需的列是否存在
    if 'month' not in df.columns or 'title' not in df.columns:
        print("  ❌ 错误: 数据中缺少 'month' 或 'title' 列")
        return
    
    # ==================== 步骤3: 统计每月高频词 ====================
    print(f"\n【步骤3】统计每月高频词（Top {top_n}）...")
    
    results = []
    months = sorted(df['month'].unique())
    print(f"  共 {len(months)} 个月份: {', '.join(months)}\n")
    
    for month in months:
        print(f"  处理 {month}...", end=' ')
        
        # 获取该月的所有标题
        month_titles = df[df['month'] == month]['title'].dropna()
        
        # 对每个标题进行分词，然后过滤
        import jieba
        
        # 加载自定义词典，确保专有名词完整
        custom_words = [
            # 体育赛事
            '全运会', '十五运会', '十五届全运会', '残运会', '特奥会',
            '亚运会', '奥运会', '世界杯', '锦标赛',
            # 区域发展
            '粤港澳大湾区', '大湾区', '前海', '横琴', '南沙',
            '珠三角', '长三角', '京津冀', '成渝',
            # 会议展会
            '广交会', '两会', '四次会议', '十四届', '人大会议', '政协会议',
            '中央经济工作会议', '省委全会', '市委全会',
            '党代会', '人代会', '政协会',
            # 政策概念
            '高质量', '高质量发展', '现代化', '中国式现代化',
            '新发展格局', '新发展理念', '双循环',
            '共同富裕', '乡村振兴', '生态文明',
            # 科技产业
            '人工智能', 'AI', '数字经济', '科技创新', '智能制造',
            '集成电路', '生物医药', '新能源汽车', '低空经济',
            '大数据', '云计算', '物联网', '区块链', '元宇宙',
            '5G', '6G', '芯片', '半导体',
            # 节庆活动
            '新春', '春节', '元宵', '中秋', '国庆',
            '花市', '庙会', '灯会', '春晚',
            # 经济金融
            '股市', '楼市', '房市', '债市', '汇市',
            'GDP', 'CPI', 'PPI', 'PMI',
            # 其他专有名词
            '广货', '粤菜', '岭南', '珠澳', '深港',
            '一带一路', '自贸区', '保税区', '开发区',
        ]
        for word in custom_words:
            jieba.add_word(word)
        
        all_words = []
        skipped_count = 0
        
        for title in month_titles:
            if isinstance(title, str) and title.strip():
                # 对标题进行分词
                words = jieba.cut(title)
                for word in words:
                    word = word.strip()
                    if word and not filter_word(word, all_stopwords):
                        all_words.append(word)
                    else:
                        skipped_count += 1
        
        # 统计词频
        word_counts = Counter(all_words)
        
        # 强制输出TOP 10（即使某些词频次较低）
        if not word_counts:
            print(f"⚠ 警告: {month} 没有有效关键词")
            continue
                
        # 获取所有词，按频次降序排列
        all_ranked_words = word_counts.most_common()
                
        # 动态阈值（仅用于参考，不影响输出数量）
        all_freqs = list(word_counts.values())
        max_freq = max(all_freqs)
        min_threshold = max(8, max_freq * 0.5)
                
        # 强制取TOP 10
        top_words = all_ranked_words[:10]
                
        # 如果词数不足10个，有多少取多少
        if len(top_words) < 10:
            print(f"⚠ 注意: {month} 只有 {len(top_words)} 个有效关键词（不足10个）")
        
        # 添加到结果列表
        for rank, (word, freq) in enumerate(top_words, 1):
            results.append({
                'month': month,
                'rank': rank,
                'word': word,
                'frequency': freq
            })
        
        print(f"✓ (总词数: {len(all_words)}, 过滤: {skipped_count}, 输出: {len(top_words)}个)")
        
        # 控制台输出该月的热点词
        print(f"    {'排名':<4} {'关键词':<15} {'频次':<8}")
        print(f"    {'-'*30}")
        for rank, (word, freq) in enumerate(top_words, 1):
            print(f"    {rank:<4} {word:<15} {freq:<8}")
        print()
    
    # ==================== 步骤4: 保存结果 ====================
    print(f"\n【步骤4】保存结果到 {output_file}")
    
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"  ✓ 已保存 {len(result_df)} 条记录")
    
    # ==================== 步骤5: 统计摘要 ====================
    print(f"\n{'='*70}")
    print("处理完成！")
    print(f"{'='*70}")
    print(f"  输入文件: {input_file}")
    print(f"  输出文件: {output_file}")
    print(f"  处理月份: {len(months)} 个")
    print(f"  总关键词数: {len(result_df)} 条")
    print(f"  停用词总数: {len(all_stopwords)} 个")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    # 执行热点话题提取
    extract_monthly_topics(
        input_file='news_cleaned.csv',
        output_file='monthly_hot_topics.csv',
        top_n=10
    )
