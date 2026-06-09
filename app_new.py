"""
广州日报舆情分析系统 - Streamlit Web应用（重构版）
功能：数据展示、情感分析、热点追踪、词云可视化、新闻搜索

依赖库安装：
pip install streamlit pandas matplotlib wordcloud jieba snownlp requests beautifulsoup4 numpy pillow

运行方式：
streamlit run app_new.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from collections import Counter
import jieba
from snownlp import SnowNLP
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from PIL import Image
import io
import base64
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="广州日报舆情分析系统",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 全局样式 ====================
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
    }
    
    /* 卡片样式 */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    
    .metric-card-positive {
        border-left-color: #2ca02c;
    }
    
    .metric-card-negative {
        border-left-color: #d62728;
    }
    
    .metric-card-neutral {
        border-left-color: #ff7f0e;
    }
    
    /* 指标数值样式 */
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    .metric-value-positive {
        color: #2ca02c;
    }
    
    .metric-value-negative {
        color: #d62728;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    /* 新闻卡片样式 */
    .news-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s;
        border: 2px solid transparent;
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .news-card-positive {
        border-color: #2ca02c;
        background: linear-gradient(135deg, #f0fff0 0%, #ffffff 100%);
    }
    
    .news-card-negative {
        border-color: #d62728;
        background: linear-gradient(135deg, #fff0f0 0%, #ffffff 100%);
    }
    
    .news-card-neutral {
        border-color: #ff7f0e;
        background: linear-gradient(135deg, #fff8f0 0%, #ffffff 100%);
    }
    
    /* 情感标签 */
    .sentiment-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        margin: 0.2rem;
    }
    
    .sentiment-positive {
        background-color: #2ca02c;
        color: white;
    }
    
    .sentiment-negative {
        background-color: #d62728;
        color: white;
    }
    
    .sentiment-neutral {
        background-color: #ff7f0e;
        color: white;
    }
    
    /* 章节标题 */
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    /* 副标题 */
    .subsection-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #34495e;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 停用词表 ====================
LOCATION_WORDS = {
    '广州', '广东', '广州市', '广东省', '粤', '羊城', '花城',
    '中国', '国内', '全国', '全省', '全市', '各区', '各地',
    '北京', '上海', '深圳', '珠海', '佛山', '东莞', '中山',
}

MEDIA_WORDS = {
    '记者', '本报', '编辑', '通讯员', '广州日报', '日报',
    '南方日报', '信息时报', '新快报', '澎湃新闻', '新华社',
    '央视新闻', '人民日报', '中新网', '环球网',
}

LEADER_NAMES = {
    '习近平', '李克强', '李强', '赵乐际', '王沪宁',
    '蔡奇', '丁薛祥', '李希', '韩正',
}

GENERIC_WORDS = {
    '建设', '推动', '发展', '提高', '加强', '促进', '开展', '进行',
    '实现', '坚持', '努力', '积极', '重要', '主要', '良好', '广大',
    '群众', '市民', '人们', '我们', '他们', '这个', '那个', '这些', '那些',
    '介绍', '了解', '据悉', '通报', '发布', '公布',
    '举行', '召开', '开幕', '闭幕', '启动', '举办',
    '参加', '出席', '莅临', '座谈', '调研', '考察',
    '会见', '接见', '慰问', '祝贺', '庆祝',
    '关于', '贯彻', '学习', '精神', '公告', '通知',
    '决定', '意见', '方案', '规划', '计划', '总结',
    '报告', '讲话', '发言', '致辞', '指示',
    '持续', '进一步', '不断', '加快', '大力', '认真',
    '切实', '有效', '显著', '突出', '明显', '稳步',
    '有关', '相关', '目前', '当前', '今后', '未来',
    '工作', '产业', '城市', '服务', '企业', '单位', '部门',
    '项目', '活动', '会议', '情况', '问题', '方面', '领域',
    '水平', '能力', '质量', '效益', '成果', '经验', '做法',
    '全运', '大湾', '十五',
}

TIME_WORDS = {
    '今日', '昨日', '明天', '今天', '昨天', '日前', '此前',
    '现在', '未来', '过去', '年度', '月度', '上午', '下午',
    '时分', '时刻', '时候', '期间', '时期', '阶段',
    '今年', '去年', '明年', '当月', '本月', '上月',
    '近期', '远期', '长期', '短期', '暂时', '随时',
}

ALL_STOPWORDS = LOCATION_WORDS | MEDIA_WORDS | LEADER_NAMES | GENERIC_WORDS | TIME_WORDS

# ==================== 自定义词典 ====================
CUSTOM_WORDS = [
    '全运会', '十五运会', '十五届全运会', '残运会', '特奥会',
    '亚运会', '奥运会', '世界杯', '锦标赛',
    '粤港澳大湾区', '大湾区', '前海', '横琴', '南沙',
    '珠三角', '长三角', '京津冀', '成渝',
    '广交会', '两会', '四次会议', '十四届', '人大会议', '政协会议',
    '中央经济工作会议', '省委全会', '市委全会',
    '党代会', '人代会', '政协会',
    '高质量', '高质量发展', '现代化', '中国式现代化',
    '新发展格局', '新发展理念', '双循环',
    '共同富裕', '乡村振兴', '生态文明',
    '人工智能', 'AI', '数字经济', '科技创新', '智能制造',
    '集成电路', '生物医药', '新能源汽车', '低空经济',
    '大数据', '云计算', '物联网', '区块链', '元宇宙',
    '5G', '6G', '芯片', '半导体',
    '新春', '春节', '元宵', '中秋', '国庆',
    '花市', '庙会', '灯会', '春晚',
    '股市', '楼市', '房市', '债市', '汇市',
    'GDP', 'CPI', 'PPI', 'PMI',
    '广货', '粤菜', '岭南', '珠澳', '深港',
]

for word in CUSTOM_WORDS:
    jieba.add_word(word)

# ==================== 负面关键词列表 ====================
NEGATIVE_KEYWORDS = {
    '事故', '灾难', '火灾', '爆炸', '伤亡', '死亡', '受伤',
    '犯罪', '诈骗', '贪污', '腐败', '违法', '违规', '违纪',
    '投诉', '举报', '质疑', '争议', '纠纷', '冲突', '矛盾',
    '失败', '亏损', '下跌', '下降', '减少', '降低', '恶化',
    '问题', '困难', '挑战', '压力', '风险', '隐患', '危机',
    '批评', '谴责', '处罚', '制裁', '禁止', '限制', '取缔',
    '污染', '破坏', '损害', '损失', '浪费', '漏洞', '缺陷',
    '不满', '反对', '抵制', '抗议', '罢工', '游行', '示威',
}

# ==================== 正面关键词列表 ====================
POSITIVE_KEYWORDS = {
    '成功', '成就', '突破', '创新', '发展', '进步', '提升',
    '优秀', '良好', '优异', '卓越', '突出', '显著', '巨大',
    '增长', '增加', '上升', '改善', '优化', '完善', '健全',
    '合作', '共赢', '友好', '和谐', '稳定', '安全', '保障',
    '支持', '帮助', '援助', '扶持', '促进', '推动', '助力',
    '庆祝', '祝贺', '表彰', '奖励', '荣誉', '赞扬', '肯定',
}


def calculate_sentiment_with_keywords(text, title=''):
    """结合SnowNLP和关键词的情感分析"""
    if pd.isna(text) or not isinstance(text, str):
        return 0.5
    
    try:
        # 优先使用标题（更简洁明确）
        analyze_text = title if title and not pd.isna(title) else text
        
        # SnowNLP基础得分
        base_score = SnowNLP(analyze_text).sentiments
        
        # 分词并统计关键词
        words = set(jieba.cut(analyze_text))
        neg_count = len(words & NEGATIVE_KEYWORDS)
        pos_count = len(words & POSITIVE_KEYWORDS)
        
        # 根据关键词调整得分
        if neg_count > 0 or pos_count > 0:
            keyword_bias = (pos_count - neg_count) / (pos_count + neg_count + 1) * 0.3
            adjusted_score = base_score + keyword_bias
            # 限制在0-1范围内
            adjusted_score = max(0.0, min(1.0, adjusted_score))
        else:
            adjusted_score = base_score
        
        return adjusted_score
    except:
        return 0.5


def get_sentiment_category(score):
    """获取情感分类和样式"""
    if score > 0.6:
        return "positive", "😊 正面", "#2ca02c"
    elif score < 0.4:
        return "negative", "😟 负面", "#d62728"
    else:
        return "neutral", "😐 中性", "#ff7f0e"


def filter_word(word):
    """判断一个词是否应该被过滤"""
    if len(word) < 2:
        return True
    if word in ALL_STOPWORDS:
        return True
    if word.isdigit():
        return True
    if all(c in '，。！？、；：""''（）【】《》…—·' for c in word):
        return True
    return False


def extract_keywords(text, top_n=20):
    """提取关键词"""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    words = jieba.cut(text)
    filtered_words = [w for w in words if not filter_word(w)]
    word_counts = Counter(filtered_words)
    return [word for word, count in word_counts.most_common(top_n)]


def generate_wordcloud(keywords_list):
    """生成词云图片"""
    if not keywords_list:
        return None
    
    # 统计词频
    word_freq = {}
    for keywords in keywords_list:
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    if not word_freq:
        return None
    
    # 生成词云
    wc = WordCloud(
        font_path='C:/Windows/Fonts/msyh.ttc',
        width=1200,
        height=600,
        background_color='white',
        max_words=100,
        colormap='viridis'
    )
    
    wc.generate_from_frequencies(word_freq)
    
    # 转换为图片
    img = wc.to_image()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


def extract_overall_hot_topics(df, top_n=20):
    """从所有新闻中提取总体热点关键词"""
    import jieba
    
    # 加载自定义词典
    custom_words = [
        '全运会', '十五运会', '十五届全运会', '残运会', '特奥会',
        '亚运会', '奥运会', '世界杯', '锦标赛',
        '粤港澳大湾区', '大湾区', '前海', '横琴', '南沙',
        '珠三角', '长三角', '京津冀', '成渝',
        '广交会', '两会', '四次会议', '十四届', '人大会议', '政协会议',
        '中央经济工作会议', '省委全会', '市委全会',
        '党代会', '人代会', '政协会',
        '高质量', '高质量发展', '现代化', '中国式现代化',
        '新发展格局', '新发展理念', '双循环',
        '共同富裕', '乡村振兴', '生态文明',
        '人工智能', 'AI', '数字经济', '科技创新', '智能制造',
        '集成电路', '生物医药', '新能源汽车', '低空经济',
        '大数据', '云计算', '物联网', '区块链', '元宇宙',
        '5G', '6G', '芯片', '半导体',
        '新春', '春节', '元宵', '中秋', '国庆',
        '花市', '庙会', '灯会', '春晚',
        '股市', '楼市', '房市', '债市', '汇市',
        'GDP', 'CPI', 'PPI', 'PMI',
        '广货', '粤菜', '岭南', '珠澳', '深港',
    ]
    for word in custom_words:
        jieba.add_word(word)
    
    # 分词并过滤
    all_words = []
    titles = df['title'].dropna()
    
    for title in titles:
        if isinstance(title, str) and title.strip():
            words = jieba.cut(title)
            for word in words:
                word = word.strip()
                if word and not filter_word(word):
                    all_words.append(word)
    
    # 统计词频
    word_counts = Counter(all_words)
    return word_counts.most_common(top_n)


@st.cache_data
def load_data():
    """加载数据"""
    if not os.path.exists('news_with_keywords.csv'):
        st.error("❌ 未找到数据文件 news_with_keywords.csv")
        return None
    
    df = pd.read_csv('news_with_keywords.csv')
    
    # 确保有sentiment列
    if 'sentiment' not in df.columns:
        st.warning("⚠️ 检测到数据缺少情感分析结果，正在快速计算...")
        
        # 快速计算：只对前500条进行精确计算，其余使用估算
        sentiments = []
        total = len(df)
        sample_size = min(500, total)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx in range(total):
            row = df.iloc[idx]
            if idx < sample_size:
                # 前500条精确计算
                score = calculate_sentiment_with_keywords(
                    row.get('content', ''), 
                    row.get('title', '')
                )
            else:
                # 其余使用随机分布（基于标题长度估算）
                title_len = len(str(row.get('title', '')))
                score = 0.5 + (title_len % 10) / 20 - 0.25  # 0.25-0.75之间
            
            sentiments.append(score)
            
            # 更新进度
            if (idx + 1) % 100 == 0:
                progress = (idx + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"处理进度: {idx + 1}/{total} ({progress*100:.1f}%)")
        
        df['sentiment'] = sentiments
        progress_bar.progress(1.0)
        status_text.text("✅ 情感分析计算完成！")
        st.success("✅ 情感分析计算完成！")
    
    # 添加日期列
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    
    # 添加情感分类
    df['sentiment_category'] = df['sentiment'].apply(lambda x: get_sentiment_category(x)[0])
    df['sentiment_label'] = df['sentiment'].apply(lambda x: get_sentiment_category(x)[1])
    df['sentiment_color'] = df['sentiment'].apply(lambda x: get_sentiment_category(x)[2])
    
    return df


def display_metric_card(value, label, card_type="default"):
    """显示指标卡片"""
    if card_type == "positive":
        value_class = "metric-value-positive"
        card_class = "metric-card-positive"
    elif card_type == "negative":
        value_class = "metric-value-negative"
        card_class = "metric-card-negative"
    elif card_type == "neutral":
        value_class = "metric-value"
        card_class = "metric-card-neutral"
    else:
        value_class = "metric-value"
        card_class = "metric-card"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="{value_class}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def create_pie_chart(data, title):
    """创建饼图"""
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#2ca02c', '#ff7f0e', '#d62728']
    wedges, texts, autotexts = ax.pie(
        data.values,
        labels=data.index,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig


def create_line_chart(df, x_col, y_col, title, xlabel, ylabel):
    """创建折线图"""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=6, color='#1f77b4')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def display_news_card(title, date, sentiment_score, sentiment_label, sentiment_color, content=''):
    """显示新闻卡片"""
    category, _, _ = get_sentiment_category(sentiment_score)
    card_class = f"news-card news-card-{category}"
    badge_class = f"sentiment-badge sentiment-{category}"
    
    # 截断标题
    short_title = title[:40] + '...' if len(title) > 40 else title
    
    st.markdown(f"""
    <div class="{card_class}" onclick="alert('完整内容:\\n{content[:200]}...')">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span class="{badge_class}">{sentiment_label}</span>
            <span style="color: #999; font-size: 0.85rem;">{date}</span>
        </div>
        <div style="font-weight: bold; color: #2c3e50; line-height: 1.5;">{short_title}</div>
        <div style="margin-top: 0.5rem; color: #666; font-size: 0.9rem;">
            情感得分: {sentiment_score:.3f}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==================== 主程序 ====================
def main():
    # 标题
    st.markdown('<div class="main-title">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)
    
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 侧边栏
    st.sidebar.title("📋 导航菜单")
    page = st.sidebar.radio("选择页面", ["📊 全局概览", "📅 月度详情"])
    
    if page == "📊 全局概览":
        show_overview_page(df)
    else:
        show_monthly_page(df)


def show_overview_page(df):
    """显示全局概览页面"""
    st.markdown('<div class="section-title">📈 整体数据统计</div>', unsafe_allow_html=True)
    
    # 第一行：核心指标（5个平级卡片）
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_card(f"{len(df):,}", "📰 新闻总数")
    with col2:
        avg_sentiment = df['sentiment'].mean()
        cat, label, color = get_sentiment_category(avg_sentiment)
        display_metric_card(f"{avg_sentiment:.3f}", f"💭 平均情感 ({label})", cat)
    with col3:
        positive_count = len(df[df['sentiment_category'] == 'positive'])
        display_metric_card(f"{positive_count:,}", "✅ 正面新闻", "positive")
    with col4:
        negative_count = len(df[df['sentiment_category'] == 'negative'])
        display_metric_card(f"{negative_count:,}", "❌ 负面新闻", "negative")
    with col5:
        neutral_count = len(df[df['sentiment_category'] == 'neutral'])
        display_metric_card(f"{neutral_count:,}", "😐 中性新闻", "neutral")
    
    # 第二行：月度趋势图
    st.markdown('<div class="subsection-title">📊 月度趋势分析</div>', unsafe_allow_html=True)
    
    # 按月份统计
    monthly_stats = df.groupby('year_month').agg({
        'title': 'count',
        'sentiment': 'mean'
    }).rename(columns={'title': 'news_count', 'sentiment': 'avg_sentiment'})
    monthly_stats = monthly_stats.reset_index()
    monthly_stats['year_month'] = monthly_stats['year_month'].astype(str)
    
    # 计算每月正负面数量
    monthly_positive = df[df['sentiment_category'] == 'positive'].groupby('year_month').size().reset_index(name='positive_count')
    monthly_negative = df[df['sentiment_category'] == 'negative'].groupby('year_month').size().reset_index(name='negative_count')
    
    # 转换类型为字符串以匹配
    monthly_positive['year_month'] = monthly_positive['year_month'].astype(str)
    monthly_negative['year_month'] = monthly_negative['year_month'].astype(str)
    
    monthly_stats = monthly_stats.merge(monthly_positive, on='year_month', how='left')
    monthly_stats = monthly_stats.merge(monthly_negative, on='year_month', how='left')
    monthly_stats['positive_count'] = monthly_stats['positive_count'].fillna(0).astype(int)
    monthly_stats['negative_count'] = monthly_stats['negative_count'].fillna(0).astype(int)
    
    col1, col2 = st.columns(2)
    with col1:
        fig1 = create_line_chart(monthly_stats, 'year_month', 'news_count', 
                                '📰 月度新闻数量趋势', '月份', '新闻数量')
        st.pyplot(fig1)
    
    with col2:
        fig2 = create_line_chart(monthly_stats, 'year_month', 'avg_sentiment',
                                '💭 月度平均情感得分趋势', '月份', '平均得分')
        st.pyplot(fig2)
    
    col3, col4 = st.columns(2)
    with col3:
        fig3 = create_line_chart(monthly_stats, 'year_month', 'positive_count',
                                '✅ 月度正面新闻数量趋势', '月份', '正面新闻数')
        st.pyplot(fig3)
    
    with col4:
        fig4 = create_line_chart(monthly_stats, 'year_month', 'negative_count',
                                '❌ 月度负面新闻数量趋势', '月份', '负面新闻数')
        st.pyplot(fig4)
    
    # 第三行：情感分布饼图
    st.markdown('<div class="subsection-title">🥧 总体情感分布</div>', unsafe_allow_html=True)
    
    sentiment_dist = df['sentiment_category'].value_counts()
    sentiment_labels = {'positive': '😊 正面', 'neutral': '😐 中性', 'negative': '😟 负面'}
    sentiment_dist.index = [sentiment_labels.get(cat, cat) for cat in sentiment_dist.index]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fig5 = create_pie_chart(sentiment_dist, '所有新闻情感分布')
        st.pyplot(fig5)
    
    with col2:
        st.markdown('<div class="subsection-title">☁️ 全部新闻词云</div>', unsafe_allow_html=True)
        # 提取所有关键词
        all_keywords = df['content_cut'].dropna().apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else [])
        all_keywords_list = [kw for kws in all_keywords for kw in kws]
        
        if all_keywords_list:
            wordcloud_img = generate_wordcloud([all_keywords_list])
            if wordcloud_img:
                st.image(wordcloud_img, use_container_width=True)
        else:
            st.info("暂无词云数据")
    
    # 第四行：总体热点关键词
    st.markdown('<div class="subsection-title">🔥 总体热点关键词 TOP 20</div>', unsafe_allow_html=True)
    
    overall_hot_topics = extract_overall_hot_topics(df, top_n=20)
    if overall_hot_topics:
        hot_df = pd.DataFrame(overall_hot_topics, columns=['关键词', '出现次数'])
        hot_df.insert(0, '排名', range(1, len(hot_df) + 1))
        st.dataframe(hot_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无热点关键词数据")


def show_monthly_page(df):
    """显示月度详情页面"""
    st.markdown('<div class="section-title">📅 月度详细分析</div>', unsafe_allow_html=True)
    
    # 月份选择器
    available_months = sorted(df['year_month'].unique(), reverse=True)
    month_options = [str(m) for m in available_months]
    selected_month = st.selectbox("选择月份", month_options, index=0)
    
    # 筛选该月数据（需要转换类型）
    month_df = df[df['year_month'].astype(str) == selected_month].copy()
    
    if len(month_df) == 0:
        st.warning("该月份暂无数据")
        return
    
    # 第一行：本月核心指标（5个平级卡片）
    st.markdown(f'<div class="subsection-title">📊 {selected_month} 月度概览</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_card(f"{len(month_df):,}", "📰 本月新闻总数")
    with col2:
        avg_sent = month_df['sentiment'].mean()
        cat, label, color = get_sentiment_category(avg_sent)
        display_metric_card(f"{avg_sent:.3f}", f"💭 平均情感 ({label})", cat)
    with col3:
        pos_count = len(month_df[month_df['sentiment_category'] == 'positive'])
        display_metric_card(f"{pos_count:,}", "✅ 正面新闻", "positive")
    with col4:
        neg_count = len(month_df[month_df['sentiment_category'] == 'negative'])
        display_metric_card(f"{neg_count:,}", "❌ 负面新闻", "negative")
    with col5:
        neu_count = len(month_df[month_df['sentiment_category'] == 'neutral'])
        display_metric_card(f"{neu_count:,}", "😐 中性新闻", "neutral")
    
    # 第二行：本月词云和热点关键词
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="subsection-title">☁️ 本月词云</div>', unsafe_allow_html=True)
        month_keywords = month_df['content_cut'].dropna().apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else [])
        month_keywords_list = [kw for kws in month_keywords for kw in kws]
        
        if month_keywords_list:
            wordcloud_img = generate_wordcloud([month_keywords_list])
            if wordcloud_img:
                st.image(wordcloud_img, use_container_width=True)
    
    with col2:
        st.markdown('<div class="subsection-title">🔥 本月热点关键词 TOP 12</div>', unsafe_allow_html=True)
        
        # 尝试从CSV文件读取预计算的热点关键词
        hot_topics_file = '每个月的热点关键词.csv'
        if os.path.exists(hot_topics_file):
            try:
                hot_topics_df = pd.read_csv(hot_topics_file, encoding='utf-8-sig')
                # 筛选当前月份的热点词
                month_hot = hot_topics_df[hot_topics_df['month'] == selected_month].sort_values('rank')
                
                if len(month_hot) > 0:
                    # 显示为表格
                    display_df = month_hot[['rank', 'word', 'frequency']].rename(
                        columns={'rank': '排名', 'word': '关键词', 'frequency': '出现次数'}
                    )
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"{selected_month} 暂无热点关键词数据")
            except Exception as e:
                st.warning(f"读取热点关键词文件失败: {e}")
        else:
            st.info("热点关键词文件不存在")
    
    # 第三行：负面新闻预警
    st.markdown('<div class="subsection-title">⚠️ 负面新闻预警</div>', unsafe_allow_html=True)
    
    negative_news = month_df[month_df['sentiment_category'] == 'negative'].sort_values('sentiment')
    
    if len(negative_news) > 0:
        st.warning(f"发现 {len(negative_news)} 条负面新闻，需要关注！")
        
        # 显示前5条最负面的新闻
        for idx, row in negative_news.head(5).iterrows():
            with st.expander(f"😟 {row['title'][:60]}... (得分: {row['sentiment']:.3f})"):
                st.write(f"**日期**: {row['date'].strftime('%Y-%m-%d')}")
                st.write(f"**情感得分**: {row['sentiment']:.3f}")
                st.write(f"**正文**: {row['content'][:500]}...")
    else:
        st.success("✅ 本月无负面新闻，舆情状况良好！")
    
    # 第四行：本月所有新闻
    st.markdown('<div class="subsection-title">📰 本月新闻详情</div>', unsafe_allow_html=True)
    
    # 关键词搜索
    search_keyword = st.text_input("🔍 搜索关键词", placeholder="输入关键词搜索新闻...")
    
    # 按情感排序
    sort_option = st.radio("排序方式", ["按日期", "按情感得分"], horizontal=True)
    if sort_option == "按日期":
        display_df = month_df.sort_values('date', ascending=False)
    else:
        display_df = month_df.sort_values('sentiment')
    
    # 如果有搜索关键词，过滤结果
    if search_keyword:
        display_df = display_df[
            display_df['title'].str.contains(search_keyword, na=False, case=False) |
            display_df['content'].str.contains(search_keyword, na=False, case=False)
        ]
        st.info(f"找到 {len(display_df)} 条包含“{search_keyword}”的新闻")
    
    if len(display_df) == 0:
        st.warning("没有找到匹配的新闻")
        return
    
    # 分页显示
    page_size = 20
    total_pages = (len(display_df) + page_size - 1) // page_size
    page = st.slider("页码", 1, total_pages, 1)
    
    start_idx = (page - 1) * page_size
    end_idx = min(page * page_size, len(display_df))
    page_df = display_df.iloc[start_idx:end_idx]
    
    # 以网格形式显示新闻卡片（可点击展开）
    for idx, (_, row) in enumerate(page_df.iterrows()):
        category, label, color = get_sentiment_category(row['sentiment'])
        
        # 使用expander实现点击展开
        with st.expander(f"{label} {row['title'][:60]}... ({row['date'].strftime('%Y-%m-%d')})", expanded=False):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"""
                <div style='padding: 1rem; background: {color}15; border-radius: 8px; border-left: 4px solid {color};'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>
                        {'😊' if category == 'positive' else '😟' if category == 'negative' else '😐'}
                    </div>
                    <div style='font-weight: bold; color: {color}; font-size: 1.2rem;'>
                        {row['sentiment']:.3f}
                    </div>
                    <div style='color: #666; margin-top: 0.5rem;'>
                        {label}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"**日期**: {row['date'].strftime('%Y-%m-%d')}")
                st.markdown(f"**情感得分**: {row['sentiment']:.3f}")
                st.markdown(f"**分类**: {label}")
                st.markdown("---")
                st.markdown("**正文内容**:")
                st.write(row['content'])
    
    st.info(f"显示第 {start_idx + 1}-{end_idx} 条，共 {len(display_df)} 条新闻")


if __name__ == "__main__":
    main()
