"""
广州日报舆情分析系统 - 云端数据版
从GitHub读取最新数据，支持自动更新
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
import io
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
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
    /* 主标题 */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin: 1rem 0;
        padding: 1rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    /* 段落标题 */
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        padding: 0.5rem;
        border-left: 5px solid #1f77b4;
        padding-left: 1rem;
    }
    
    /* 子标题 */
    .subsection-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #34495e;
        margin: 1rem 0 0.8rem 0;
    }
    
    /* 新闻卡片 */
    .news-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .news-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 停用词和关键词 ====================
STOPWORDS = set()
try:
    with open('stopwords.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                STOPWORDS.add(word)
except:
    pass

# 地域名称
LOCATION_WORDS = {'广州', '广东', '中国', '全国', '全省', '全市', '粤港澳大湾区', '大湾区', '珠三角'}
STOPWORDS.update(LOCATION_WORDS)

# 媒体相关
MEDIA_WORDS = {'记者', '本报', '通讯员', '编辑', '来源', '图片', '视频', '直播', '报道', '采访', '讯'}
STOPWORDS.update(MEDIA_WORDS)

# 领导人姓名
LEADER_NAMES = {'习近平', '李克强', '汪洋', '王沪宁', '赵乐际', '李希', '韩正', '丁薛祥'}
STOPWORDS.update(LEADER_NAMES)

# 通用无意义词
GENERIC_WORDS = {
    '建设', '推动', '发展', '促进', '加强', '提高', '推进', '实施',
    '开展', '组织', '召开', '举行', '会议', '工作', '活动', '项目',
    '服务', '管理', '监督', '检查', '落实', '完成', '实现', '目标',
    '任务', '要求', '指出', '强调', '表示', '认为', '说明', '介绍',
    '进一步', '持续', '不断', '全面', '深入', '积极', '大力', '加快'
}
STOPWORDS.update(GENERIC_WORDS)

# 时间词
TIME_WORDS = {
    '今日', '昨天', '昨日', '前天', '今天', '明天', '后天',
    '今年', '去年', '明年', '本月', '上月', '下月',
    '近日', '近期', '目前', '当前', '现在', '当时', '曾经'
}
STOPWORDS.update(TIME_WORDS)

ALL_STOPWORDS = STOPWORDS

# 正面/负面关键词
POSITIVE_KEYWORDS = {
    '成功', '优秀', '创新', '突破', '进步', '成就', '发展', '繁荣',
    '胜利', '辉煌', '领先', '优质', '高效', '卓越', '杰出', '先进',
    '改善', '提升', '增长', '扩大', '完善', '优化', '升级', '转型'
}

NEGATIVE_KEYWORDS = {
    '失败', '问题', '困难', '挑战', '危机', '风险', '损失', '下降',
    '减少', '恶化', '冲突', '矛盾', '争议', '投诉', '事故', '灾害',
    '污染', '破坏', '违规', '违法', '腐败', '贪污', '诈骗', '犯罪'
}

# ==================== 自定义词典 ====================
CUSTOM_DICT = [
    '十五运会', '全运会', '大湾区', '粤港澳', '南沙', '前海', '横琴',
    '广交会', '花城', '羊城', '珠水', '白云山', '珠江新城',
    '高质量发展', '新质生产力', '数字化转型', '智能制造',
    '人工智能', '区块链', '云计算', '大数据', '物联网', '5G'
]

for word in CUSTOM_DICT:
    jieba.add_word(word)

# ==================== 工具函数 ====================
def get_sentiment_info(score):
    """获取情感信息"""
    if score >= 0.6:
        return 'positive', '正面', '#2ca02c'
    elif score <= 0.4:
        return 'negative', '负面', '#d62728'
    else:
        return 'neutral', '中性', '#ff7f0e'

def calculate_sentiment_v2(text, title=''):
    """改进版情感分析 - 确保正面新闻不被误判"""
    if pd.isna(text) or not isinstance(text, str):
        return 0.5
    
    try:
        # 优先使用标题（更简洁明确）
        analyze_text = title if title and not pd.isna(title) else text
        
        # SnowNLP基础得分
        base_score = SnowNLP(analyze_text).sentiments
        
        # 分词并统计关键词
        words = list(jieba.cut(analyze_text))
        word_set = set(words)
        
        neg_count = len(word_set & NEGATIVE_KEYWORDS)
        pos_count = len(word_set & POSITIVE_KEYWORDS)
        
        # 改进策略：官方新闻偏向正面
        # 1. 有明确正面词且无负面词 -> 强制正面
        if pos_count > 0 and neg_count == 0:
            return max(0.65, base_score + 0.2)  # 最低0.65
        
        # 2. 有明确负面词且无正面词 -> 负面
        if neg_count >= 2 and pos_count == 0:
            return min(0.35, base_score - 0.2)  # 最高0.35
        
        # 3. 正面词多于负面词 -> 正面
        if pos_count > neg_count:
            return max(0.55, base_score + 0.1)
        
        # 4. 负面词多于正面词 -> 负面
        if neg_count > pos_count:
            return min(0.45, base_score - 0.1)
        
        # 5. 没有明显情感词 -> 信任SnowNLP但偏向中性偏正
        final_score = base_score
        if final_score > 0.7:
            final_score = 0.65  # 降低过度乐观
        elif final_score < 0.3:
            final_score = 0.35  # 降低过度悲观
        elif 0.4 <= final_score <= 0.6:
            final_score = 0.55  # 默认偏正面
        
        return round(final_score, 3)
        
    except:
        return 0.5

def generate_wordcloud_from_titles(titles):
    """从标题列表生成词云"""
    if not titles or len(titles) == 0:
        return None
    
    # 分词并过滤
    all_words = []
    for title in titles:
        if isinstance(title, str) and title.strip():
            words = jieba.cut(title)
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in ALL_STOPWORDS and not word.isdigit():
                    all_words.append(word)
    
    if not all_words:
        return None
    
    # 统计词频
    word_freq = Counter(all_words)
    
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
    img = wc.to_image()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()

def extract_hot_topics_from_titles(titles, top_n=20):
    """从标题提取热点关键词（与extract脚本逻辑一致）"""
    if not titles or len(titles) == 0:
        return []
    
    # 分词并过滤
    all_words = []
    for title in titles:
        if isinstance(title, str) and title.strip():
            words = jieba.cut(title)
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in ALL_STOPWORDS and not word.isdigit():
                    all_words.append(word)
    
    if not all_words:
        return []
    
    # 统计词频
    word_counts = Counter(all_words)
    
    # 动态阈值
    max_freq = max(word_counts.values())
    min_threshold = max(8, max_freq * 0.5)
    
    # 筛选
    filtered = [(word, freq) for word, freq in word_counts.most_common() if freq >= min_threshold]
    
    return filtered[:top_n]

def display_metric_simple(value, label, value_type="default"):
    """显示简单指标（使用Streamlit原生metric，样式统一）"""
    st.metric(label=label, value=value)

def display_news_card(title, date, score, content):
    """显示新闻卡片（带情感颜色边框和emoji）"""
    cat, label, color = get_sentiment_info(score)
    
    # 确定emoji
    emoji_map = {'positive': '😊', 'negative': '😞', 'neutral': '😐'}
    emoji = emoji_map.get(cat, '😐')
    
    # 使用expander实现点击展开
    with st.expander(f"{emoji} {title[:80]}... ({label})", expanded=False):
        # 左侧：彩色情感方块
        col_left, col_right = st.columns([1, 4])
        
        with col_left:
            st.markdown(f"""
            <div style="
                background: {color};
                color: white;
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            ">
                <div style="font-size: 2rem;">{emoji}</div>
                <div style="margin-top: 0.5rem;">{label}</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem;">{score:.3f}</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem;">{date}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            st.markdown(f"""
            <div style="
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 8px;
                line-height: 1.8;
            ">
                <strong>正文：</strong><br><br>
                {content}
            </div>
            """, unsafe_allow_html=True)

def create_line_chart(df, x_col, y_col, title, x_label, y_label):
    """创建折线图"""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=6, color='#1f77b4')
    ax.set_xlabel(x_label, fontsize=11)
    ax.set_ylabel(y_label, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def create_pie_chart(data, title):
    """创建饼图"""
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = ['#2ca02c', '#ff7f0e', '#d62728']
    wedges, texts, autotexts = ax.pie(
        data.values, 
        labels=data.index, 
        autopct='%1.1f%%',
        colors=colors[:len(data)],
        startangle=90
    )
    ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

# ==================== 数据加载（从云端）====================
# GitHub Raw URL（需要替换为您的实际URL）
GITHUB_RAW_URL = "https://raw.githubusercontent.com/your-username/your-repo/main/news_with_keywords.csv"

@st.cache_data(ttl=3600)  # 缓存1小时
def load_data_from_cloud():
    """从云端加载数据"""
    try:
        # 尝试从GitHub读取
        df = pd.read_csv(GITHUB_RAW_URL, encoding='utf-8-sig')
        st.success("✅ 已从云端加载最新数据")
        return df
    except Exception as e:
        st.warning(f"⚠️ 无法从云端加载数据: {e}")
        st.info("💡 尝试使用本地数据...")
        
        # Fallback: 使用本地数据
        if os.path.exists('news_with_keywords.csv'):
            df = pd.read_csv('news_with_keywords.csv', encoding='utf-8-sig')
            st.success("✅ 已使用本地数据")
            return df
        else:
            st.error("❌ 未找到任何数据源")
            return None

def process_data(df):
    """处理数据：添加情感分析、日期等"""
    if df is None:
        return None
    
    # 计算情感（如果还没有）
    if 'sentiment' not in df.columns:
        st.info("⏳ 正在计算情感分析...")
        sentiments = []
        total = len(df)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, row in df.iterrows():
            score = calculate_sentiment_v2(row.get('content', ''), row.get('title', ''))
            sentiments.append(score)
            
            if (idx + 1) % 100 == 0:
                progress = (idx + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"处理进度: {idx + 1}/{total} ({progress*100:.1f}%)")
        
        df['sentiment'] = sentiments
        progress_bar.progress(1.0)
        status_text.text("✅ 情感分析完成！")
    
    # 添加日期和月份
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')
    
    # 添加情感分类
    df['sentiment_category'] = df['sentiment'].apply(lambda x: get_sentiment_info(x)[0])
    
    return df

# ==================== 全局概览页 ====================
def show_overview(df):
    """全局概览"""
    st.markdown('<div class="section-title">📈 整体数据统计</div>', unsafe_allow_html=True)
    
    # 5个平级指标
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_simple(f"{len(df):,}", "📰 新闻总数")
    with col2:
        avg = df['sentiment'].mean()
        cat, label, _ = get_sentiment_info(avg)
        display_metric_simple(f"{avg:.3f}", f"💭 平均情感 ({label})", cat)
    with col3:
        pos = len(df[df['sentiment_category'] == 'positive'])
        display_metric_simple(f"{pos:,}", "✅ 正面新闻", "positive")
    with col4:
        neg = len(df[df['sentiment_category'] == 'negative'])
        display_metric_simple(f"{neg:,}", "❌ 负面新闻", "negative")
    with col5:
        neu = len(df[df['sentiment_category'] == 'neutral'])
        display_metric_simple(f"{neu:,}", "😐 中性新闻", "neutral")
    
    st.divider()
    
    # 月度趋势
    st.markdown('<div class="subsection-title">📊 月度趋势分析</div>', unsafe_allow_html=True)
    
    monthly = df.groupby('year_month').agg({
        'sentiment': 'mean',
        'title': 'count'
    }).reset_index()
    monthly.columns = ['year_month', 'avg_sentiment', 'news_count']
    monthly['year_month'] = monthly['year_month'].astype(str)
    
    # 添加正负面计数
    pos_monthly = df[df['sentiment_category'] == 'positive'].groupby('year_month').size().reset_index(name='pos_count')
    neg_monthly = df[df['sentiment_category'] == 'negative'].groupby('year_month').size().reset_index(name='neg_count')
    
    monthly = monthly.merge(pos_monthly, on='year_month', how='left')
    monthly = monthly.merge(neg_monthly, on='year_month', how='left')
    monthly.fillna(0, inplace=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fig1 = create_line_chart(monthly, 'year_month', 'news_count', '📰 月度新闻数量趋势', '月份', '数量')
        st.pyplot(fig1)
    with col2:
        fig2 = create_line_chart(monthly, 'year_month', 'avg_sentiment', '💭 月度平均情感趋势', '月份', '情感得分')
        st.pyplot(fig2)
    with col3:
        fig3 = create_line_chart(monthly, 'year_month', 'pos_count', '✅ 月度正面新闻趋势', '月份', '数量')
        st.pyplot(fig3)
    with col4:
        fig4 = create_line_chart(monthly, 'year_month', 'neg_count', '❌ 月度负面新闻趋势', '月份', '数量')
        st.pyplot(fig4)
    
    # 情感分布饼图 + 总体词云
    st.markdown('<div class="subsection-title">🥧 情感分布与词云</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        sentiment_dist = df['sentiment_category'].value_counts()
        labels = {'positive': '😊 正面', 'neutral': '😐 中性', 'negative': ' 负面'}
        sentiment_dist.index = [labels.get(c, c) for c in sentiment_dist.index]
        fig5 = create_pie_chart(sentiment_dist, '总体情感分布')
        st.pyplot(fig5)
    
    with col2:
        st.markdown('<div class="subsection-title">☁️ 全部新闻词云</div>', unsafe_allow_html=True)
        wordcloud_img = generate_wordcloud_from_titles(df['title'].tolist())
        if wordcloud_img:
            st.image(wordcloud_img, use_container_width=True)
        else:
            st.info("暂无词云数据")
    
    # 总体热点关键词
    st.markdown('<div class="subsection-title">🔥 总体热点关键词 TOP 20</div>', unsafe_allow_html=True)
    
    hot_topics = extract_hot_topics_from_titles(df['title'].tolist(), top_n=20)
    if hot_topics:
        hot_df = pd.DataFrame(hot_topics, columns=['关键词', '出现次数'])
        hot_df.insert(0, '排名', range(1, len(hot_df) + 1))
        st.dataframe(hot_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无热点关键词数据")

# ==================== 月度详情页 ====================
def show_monthly(df):
    """月度详情"""
    st.markdown('<div class="section-title">📅 月度详细分析</div>', unsafe_allow_html=True)
    
    # 功能1: 月份选择器
    months = sorted(df['year_month'].unique(), reverse=True)
    month_options = [str(m) for m in months]
    selected = st.selectbox("📅 选择月份", month_options, index=0)
    
    month_df = df[df['year_month'].astype(str) == selected].copy()
    
    if len(month_df) == 0:
        st.warning("该月份暂无数据")
        return
    
    # 5个指标
    st.markdown(f'<div class="subsection-title">📊 {selected} 月度概览</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_simple(f"{len(month_df):,}", "📰 本月新闻总数")
    with col2:
        avg = month_df['sentiment'].mean()
        cat, label, _ = get_sentiment_info(avg)
        display_metric_simple(f"{avg:.3f}", f"💭 平均情感 ({label})", cat)
    with col3:
        pos = len(month_df[month_df['sentiment_category'] == 'positive'])
        display_metric_simple(f"{pos:,}", "✅ 正面新闻", "positive")
    with col4:
        neg = len(month_df[month_df['sentiment_category'] == 'negative'])
        display_metric_simple(f"{neg:,}", "❌ 负面新闻", "negative")
    with col5:
        neu = len(month_df[month_df['sentiment_category'] == 'neutral'])
        display_metric_simple(f"{neu:,}", "😐 中性新闻", "neutral")
    
    # 本月词云 + 热点关键词
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="subsection-title">☁️ 本月词云</div>', unsafe_allow_html=True)
        wordcloud_img = generate_wordcloud_from_titles(month_df['title'].tolist())
        if wordcloud_img:
            st.image(wordcloud_img, use_container_width=True)
        else:
            st.info("暂无词云数据")
    
    with col2:
        st.markdown('<div class="subsection-title">🔥 本月热点关键词 TOP 10</div>', unsafe_allow_html=True)
        
        # 实时提取热点关键词
        hot_topics = extract_hot_topics_from_titles(month_df['title'].tolist(), top_n=10)
        if hot_topics:
            hot_df = pd.DataFrame(hot_topics, columns=['关键词', '频次'])
            hot_df.insert(0, '排名', range(1, len(hot_df) + 1))
            st.dataframe(hot_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无热点关键词")
    
    # 负面新闻预警
    st.markdown('<div class="subsection-title">⚠️ 负面新闻预警</div>', unsafe_allow_html=True)
    
    negative = month_df[month_df['sentiment_category'] == 'negative'].sort_values('sentiment')
    if len(negative) > 0:
        for idx, row in negative.head(5).iterrows():
            display_news_card(row['title'], row['date'].strftime('%Y-%m-%d'), row['sentiment'], row['content'])
    else:
        st.success("✅ 本月无负面新闻")
    
    # 功能2: 关键词搜索 + 新闻展示
    st.markdown('<div class="subsection-title">📰 本月新闻详情</div>', unsafe_allow_html=True)
    
    search = st.text_input("🔍 搜索关键词", placeholder="输入关键词搜索标题和正文...")
    sort_by = st.radio("排序方式", ["按日期", "按情感得分"], horizontal=True)
    
    display_df = month_df.sort_values('date', ascending=False) if sort_by == "按日期" else month_df.sort_values('sentiment')
    
    if search:
        display_df = display_df[
            display_df['title'].str.contains(search, na=False, case=False) |
            display_df['content'].str.contains(search, na=False, case=False)
        ]
        st.info(f'找到 {len(display_df)} 条包含"{search}"的新闻')
    
    # 分页显示
    page_size = 10
    total_pages = (len(display_df) + page_size - 1) // page_size
    page = st.slider("页码", 1, total_pages, 1) if total_pages > 1 else 1
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = display_df.iloc[start_idx:end_idx]
    
    for idx, row in page_df.iterrows():
        display_news_card(
            row['title'],
            row['date'].strftime('%Y-%m-%d'),
            row['sentiment'],
            row['content']
        )

# ==================== 主程序 ====================
def main():
    # 标题
    st.markdown('<div class="main-title">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("🎯 导航")
        page = st.radio("选择页面", ["📊 全局概览", "📅 月度详情"])
        
        st.divider()
        st.info("💡 **数据来源**\n\n从云端自动获取最新数据\n\n每天凌晨2点更新")
        
        st.divider()
        st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 加载数据
    df = load_data_from_cloud()
    if df is None:
        st.error("无法加载数据，请检查网络连接或数据文件")
        return
    
    # 处理数据
    df = process_data(df)
    if df is None:
        return
    
    # 显示页面
    if page == "📊 全局概览":
        show_overview(df)
    else:
        show_monthly(df)

if __name__ == "__main__":
    main()
