"""
广州日报舆情分析系统 - 最终完整版
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
    
    .subsection-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #34495e;
        margin: 1rem 0 0.8rem 0;
    }
    
    /* 指标卡片 - 5个平级 */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        margin: 0.5rem;
        border-left: 6px solid #1f77b4;
        text-align: center;
    }
    
    .metric-card-positive {
        border-left-color: #2ca02c !important;
    }
    
    .metric-card-negative {
        border-left-color: #d62728 !important;
    }
    
    .metric-card-neutral {
        border-left-color: #ff7f0e !important;
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    
    .metric-value-positive {
        color: #2ca02c !important;
    }
    
    .metric-value-negative {
        color: #d62728 !important;
    }
    
    .metric-value-neutral {
        color: #ff7f0e !important;
    }
    
    .metric-label {
        font-size: 1.1rem;
        color: #555;
        font-weight: 500;
    }
    
    /* 新闻卡片 */
    .news-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    
    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .news-card-positive {
        border-color: #2ca02c;
    }
    
    .news-card-negative {
        border-color: #d62728;
    }
    
    .news-card-neutral {
        border-color: #ff7f0e;
    }
    
    /* 情感标签 */
    .sentiment-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        color: white;
    }
    
    .sentiment-positive {
        background-color: #2ca02c;
    }
    
    .sentiment-negative {
        background-color: #d62728;
    }
    
    .sentiment-neutral {
        background-color: #ff7f0e;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 停用词定义（与extract脚本一致） ====================
LOCATION_WORDS = {
    '广州', '广东', '广州市', '广东省', '粤', '羊城', '花城',
    '深圳', '深圳市', '珠海', '珠海市', '佛山', '佛山市',
    '中国', '北京', '上海', '天津', '重庆',
}

MEDIA_WORDS = {
    '记者', '本报', '编辑', '通讯员', '广州日报', '日报',
    '报道', '采访', '新闻', '消息', '快讯',
}

LEADER_NAMES = {
    '习近平', '李克强', '李强', '总书记', '总理', '主席'
}

GENERIC_WORDS = {
    '建设', '推动', '发展', '提高', '加强', '促进', '开展',
    '进行', '实现', '坚持', '努力', '推进', '落实', '做好',
    '完成', '实施', '执行', '组织', '安排', '部署',
    '要求', '强调', '指出', '提出', '表示', '认为', '说明',
    '举行', '召开', '开幕', '闭幕', '启动', '举办',
    '参加', '出席', '莅临', '座谈', '调研', '考察',
    '工作', '产业', '城市', '服务', '企业', '单位', '部门',
    '项目', '活动', '会议', '情况', '问题', '方面', '领域',
}

TIME_WORDS = {
    '今日', '昨日', '今天', '昨天', '日前', '此前',
    '今年', '去年', '明年', '当月', '本月', '上月',
}

ALL_STOPWORDS = LOCATION_WORDS | MEDIA_WORDS | LEADER_NAMES | GENERIC_WORDS | TIME_WORDS

# 自定义词典
CUSTOM_WORDS = [
    '全运会', '十五运会', '十五届全运会', '残运会', '特奥会',
    '粤港澳大湾区', '大湾区', '前海', '横琴', '南沙',
    '广交会', '两会', '四次会议', '十四届', '人大会议', '政协会议',
    '高质量发展', '现代化', '中国式现代化',
    '人工智能', 'AI', '数字经济', '科技创新',
    '新春', '春节', '元宵', '中秋', '国庆',
]

for word in CUSTOM_WORDS:
    jieba.add_word(word)

# ==================== 情感分析 ====================
NEGATIVE_KEYWORDS = {
    '事故', '灾难', '火灾', '爆炸', '伤亡', '死亡', '受伤',
    '犯罪', '诈骗', '贪污', '腐败', '违法', '违规',
    '投诉', '举报', '质疑', '争议', '纠纷', '冲突',
    '失败', '亏损', '下跌', '下降', '减少', '降低',
    '批评', '谴责', '处罚', '制裁', '禁止', '限制',
}

POSITIVE_KEYWORDS = {
    '成功', '成就', '突破', '创新', '发展', '进步', '提升',
    '优秀', '良好', '优异', '卓越', '突出', '显著',
    '增长', '增加', '上升', '改善', '优化', '完善',
    '合作', '共赢', '友好', '和谐', '稳定', '安全',
    '支持', '帮助', '援助', '促进', '推动', '助力',
}

def calculate_sentiment(text, title=''):
    """情感分析"""
    if pd.isna(text) or not isinstance(text, str):
        return 0.5
    
    try:
        analyze_text = title if title and not pd.isna(title) else text
        base_score = SnowNLP(analyze_text).sentiments
        
        words = set(jieba.cut(analyze_text))
        neg_count = len(words & NEGATIVE_KEYWORDS)
        pos_count = len(words & POSITIVE_KEYWORDS)
        
        if neg_count > 0 or pos_count > 0:
            bias = (pos_count - neg_count) / (pos_count + neg_count + 1) * 0.3
            score = base_score + bias
            return max(0.0, min(1.0, score))
        return base_score
    except:
        return 0.5

def get_sentiment_info(score):
    """获取情感信息"""
    if score > 0.6:
        return "positive", "😊 正面", "#2ca02c"
    elif score < 0.4:
        return "negative", "😟 负面", "#d62728"
    else:
        return "neutral", "😐 中性", "#ff7f0e"

# ==================== 词云生成 ====================
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

# ==================== 热点关键词提取 ====================
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

# ==================== 显示函数 ====================
def display_metric_card(value, label, card_type="default"):
    """显示指标卡片"""
    if card_type == "positive":
        value_class = "metric-value-positive"
        card_class = "metric-card-positive"
    elif card_type == "negative":
        value_class = "metric-value-negative"
        card_class = "metric-card-negative"
    elif card_type == "neutral":
        value_class = "metric-value-neutral"
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

def display_news_expander(title, date, score, content):
    """显示可展开的新闻"""
    cat, label, color = get_sentiment_info(score)
    
    with st.expander(f"{label} | {date} | {title[:60]}{'...' if len(title)>60 else ''}"):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"""
            <div style="background:{color};color:white;padding:1rem;border-radius:8px;text-align:center;">
                <div style="font-size:2rem;font-weight:bold;">{score:.3f}</div>
                <div style="font-size:0.9rem;margin-top:0.5rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.write(content[:500] + '...' if len(content) > 500 else content)

# ==================== 图表函数 ====================
def create_line_chart(df, x_col, y_col, title, xlabel, ylabel):
    """创建折线图"""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=6)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def create_pie_chart(data, title):
    """创建饼图"""
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#2ca02c', '#ff7f0e', '#d62728']
    ax.pie(data.values, labels=data.index, autopct='%1.1f%%', colors=colors, startangle=90)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

# ==================== 数据加载 ====================
@st.cache_data
def load_data():
    """加载数据"""
    if not os.path.exists('news_with_keywords.csv'):
        st.error("❌ 未找到 news_with_keywords.csv")
        return None
    
    df = pd.read_csv('news_with_keywords.csv')
    
    # 计算情感
    if 'sentiment' not in df.columns:
        with st.spinner('⏳ 正在计算情感分析...'):
            sentiments = []
            for idx, row in df.iterrows():
                score = calculate_sentiment(row.get('content', ''), row.get('title', ''))
                sentiments.append(score)
            df['sentiment'] = sentiments
        st.success("✅ 情感分析完成！")
    
    # 添加日期和月份
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    
    # 添加情感分类
    df['sentiment_category'] = df['sentiment'].apply(lambda x: get_sentiment_info(x)[0])
    
    return df

# ==================== 全局概览页 ====================
def show_overview(df):
    """全局概览"""
    st.markdown('<div class="section-title">📈 整体数据统计</div>', unsafe_allow_html=True)
    
    # 5个指标卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_card(f"{len(df):,}", "📰 新闻总数")
    with col2:
        avg = df['sentiment'].mean()
        cat, label, _ = get_sentiment_info(avg)
        display_metric_card(f"{avg:.3f}", f"💭 平均情感 ({label})", cat)
    with col3:
        pos = len(df[df['sentiment_category'] == 'positive'])
        display_metric_card(f"{pos:,}", "✅ 正面新闻", "positive")
    with col4:
        neg = len(df[df['sentiment_category'] == 'negative'])
        display_metric_card(f"{neg:,}", "❌ 负面新闻", "negative")
    with col5:
        neu = len(df[df['sentiment_category'] == 'neutral'])
        display_metric_card(f"{neu:,}", "😐 中性新闻", "neutral")
    
    # 月度趋势
    st.markdown('<div class="subsection-title"> 月度趋势分析</div>', unsafe_allow_html=True)
    
    monthly = df.groupby('year_month').agg({
        'title': 'count',
        'sentiment': 'mean'
    }).rename(columns={'title': 'count', 'sentiment': 'avg_sent'})
    monthly = monthly.reset_index()
    monthly['year_month'] = monthly['year_month'].astype(str)
    
    # 计算月度正负面数量
    monthly_pos = df[df['sentiment_category'] == 'positive'].groupby('year_month').size().reset_index(name='pos_count')
    monthly_neg = df[df['sentiment_category'] == 'negative'].groupby('year_month').size().reset_index(name='neg_count')
    monthly_pos['year_month'] = monthly_pos['year_month'].astype(str)
    monthly_neg['year_month'] = monthly_neg['year_month'].astype(str)
    
    monthly = monthly.merge(monthly_pos, on='year_month', how='left')
    monthly = monthly.merge(monthly_neg, on='year_month', how='left')
    monthly['pos_count'] = monthly['pos_count'].fillna(0).astype(int)
    monthly['neg_count'] = monthly['neg_count'].fillna(0).astype(int)
    
    col1, col2 = st.columns(2)
    with col1:
        fig1 = create_line_chart(monthly, 'year_month', 'count', '📰 月度新闻数量趋势', '月份', '数量')
        st.pyplot(fig1)
    with col2:
        fig2 = create_line_chart(monthly, 'year_month', 'avg_sent', ' 月度平均情感趋势', '月份', '得分')
        st.pyplot(fig2)
    
    col3, col4 = st.columns(2)
    with col3:
        fig3 = create_line_chart(monthly, 'year_month', 'pos_count', '✅ 月度正面新闻趋势', '月份', '数量')
        st.pyplot(fig3)
    with col4:
        fig4 = create_line_chart(monthly, 'year_month', 'neg_count', ' 月度负面新闻趋势', '月份', '数量')
        st.pyplot(fig4)
    
    # 情感分布饼图 + 总体词云
    st.markdown('<div class="subsection-title"> 情感分布与词云</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        sentiment_dist = df['sentiment_category'].value_counts()
        labels = {'positive': '😊 正面', 'neutral': '😐 中性', 'negative': '😟 负面'}
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
    
    # 月份选择器
    months = sorted(df['year_month'].unique(), reverse=True)
    month_options = [str(m) for m in months]
    selected = st.selectbox("选择月份", month_options, index=0)
    
    # 筛选数据
    month_df = df[df['year_month'].astype(str) == selected].copy()
    
    if len(month_df) == 0:
        st.warning("该月份暂无数据")
        return
    
    # 5个指标卡片
    st.markdown(f'<div class="subsection-title">📊 {selected} 月度概览</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_card(f"{len(month_df):,}", "📰 本月新闻总数")
    with col2:
        avg = month_df['sentiment'].mean()
        cat, label, _ = get_sentiment_info(avg)
        display_metric_card(f"{avg:.3f}", f"💭 平均情感 ({label})", cat)
    with col3:
        pos = len(month_df[month_df['sentiment_category'] == 'positive'])
        display_metric_card(f"{pos:,}", "✅ 正面新闻", "positive")
    with col4:
        neg = len(month_df[month_df['sentiment_category'] == 'negative'])
        display_metric_card(f"{neg:,}", "❌ 负面新闻", "negative")
    with col5:
        neu = len(month_df[month_df['sentiment_category'] == 'neutral'])
        display_metric_card(f"{neu:,}", "😐 中性新闻", "neutral")
    
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
        st.markdown('<div class="subsection-title"> 本月热点关键词 TOP 12</div>', unsafe_allow_html=True)
        
        # 读取预计算的热点关键词CSV
        hot_file = 'monthly_hot_topics.csv'
        if os.path.exists(hot_file):
            try:
                hot_df = pd.read_csv(hot_file, encoding='utf-8-sig')
                month_hot = hot_df[hot_df['month'] == selected].sort_values('rank').head(12)
                
                if len(month_hot) > 0:
                    display_df = month_hot[['rank', 'word', 'frequency']].rename(
                        columns={'rank': '排名', 'word': '关键词', 'frequency': '频次'}
                    )
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"{selected} 暂无热点关键词")
            except Exception as e:
                st.warning(f"读取失败: {e}")
        else:
            # 实时提取
            hot_topics = extract_hot_topics_from_titles(month_df['title'].tolist(), top_n=12)
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
            display_news_expander(row['title'], row['date'].strftime('%Y-%m-%d'), row['sentiment'], row['content'])
    else:
        st.success("✅ 本月无负面新闻")
    
    # 新闻搜索和展示
    st.markdown('<div class="subsection-title">📰 本月新闻详情</div>', unsafe_allow_html=True)
    
    search = st.text_input("🔍 搜索关键词", placeholder="输入关键词搜索新闻...")
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
        display_news_expander(
            row['title'],
            row['date'].strftime('%Y-%m-%d'),
            row['sentiment'],
            row['content']
        )

# ==================== 主程序 ====================
def main():
    st.markdown('<div class="main-title">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)
    
    df = load_data()
    if df is None:
        return
    
    st.sidebar.title("📋 导航菜单")
    page = st.sidebar.radio("选择页面", ["📊 全局概览", "📅 月度详情"])
    
    if page == "📊 全局概览":
        show_overview(df)
    else:
        show_monthly(df)

if __name__ == "__main__":
    main()
