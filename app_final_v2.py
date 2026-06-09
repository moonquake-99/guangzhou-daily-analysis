"""
广州日报舆情分析系统 - 完全修复版
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
        color: #C41E3A;  /* 中国红 */
        margin: 1rem 0;
        padding: 1rem;
        border-bottom: 3px solid #C41E3A;
        background: linear-gradient(to right, #FFF8DC, #FFFFFF, #FFF8DC);  /* 淡金色背景 */
    }
    
    /* 段落标题 */
    .section-title {
        font-size: 1.6rem;  /* 统一字体大小 */
        font-weight: bold;
        color: #C41E3A;  /* 中国红 */
        margin: 1.5rem 0 1rem 0;
        padding: 0.5rem 1rem;
        border-left: 5px solid #C41E3A;
        background: linear-gradient(to right, #FFF8DC, #FFFFFF);  /* 淡金色渐变 */
    }
    
    .subsection-title {
        font-size: 1.6rem;  /* 与section-title相等 */
        font-weight: bold;
        color: #8B4513;  /* 金棕色 */
        margin: 1rem 0 0.8rem 0;
        padding: 0.3rem 0.8rem;
        border-bottom: 2px solid #DAA520;  /* 金色底线 */
    }
    
    /* 指标数值样式 - 统一字体 */
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.3rem;
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
        font-size: 1rem;
        color: #666;
        font-weight: 500;
    }
    
    /* 指标卡片 - 政府网站风格 */
    .metric-card {
        background: linear-gradient(135deg, #FFF8DC 0%, #FFFFFF 100%);  /* 淡金色渐变 */
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 3px 10px rgba(196, 30, 58, 0.15);  /* 中国红阴影 */
        margin: 0.5rem;
        border-left: 6px solid #C41E3A;  /* 中国红边框 */
        text-align: center;
        transition: all 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(196, 30, 58, 0.25);
    }
    
    /* 新闻卡片 - 政府网站风格 */
    .news-card {
        background: linear-gradient(90deg, #FFF8DC 0%, #FFFFFF 100%);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 6px rgba(196, 30, 58, 0.1);
        cursor: pointer;
        border-left: 5px solid #C41E3A;  /* 中国红 */
        transition: all 0.3s;
    }
    
    .news-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(196, 30, 58, 0.2);
    }
    
    .news-card-positive {
        border-left-color: #2ca02c !important;  /* 绿色-正面 */
        background: linear-gradient(90deg, rgba(44,160,44,0.08) 0%, white 100%);
    }
    
    .news-card-negative {
        border-left-color: #d62728 !important;  /* 红色-负面 */
        background: linear-gradient(90deg, rgba(214,39,40,0.08) 0%, white 100%);
    }
    
    .news-card-neutral {
        border-left-color: #DAA520 !important;  /* 金色-中性 */
        background: linear-gradient(90deg, rgba(218,165,32,0.08) 0%, white 100%);
    }
    
    /* 情感标签 - 政府网站风格 */
    .sentiment-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .sentiment-positive {
        background: linear-gradient(135deg, #2ca02c 0%, #228B22 100%);  /* 绿色渐变 */
    }
    
    .sentiment-negative {
        background: linear-gradient(135deg, #d62728 0%, #C41E3A 100%);  /* 红色渐变 */
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, #DAA520 0%, #B8860B 100%);  /* 金色渐变 */
    }
</style>
""", unsafe_allow_html=True)

# ==================== 停用词定义 ====================
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

# ==================== 改进的情感分析 ====================
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
        if neg_count > 0 and pos_count == 0:
            if neg_count >= 2:
                return min(0.35, base_score - 0.2)  # 最高0.35
            else:
                return 0.45  # 单个负面词，偏中性
        
        # 3. 正面词多于负面词 -> 正面
        if pos_count > neg_count and pos_count >= 2:
            return max(0.6, base_score + 0.15)
        
        # 4. 负面词多于正面词 -> 负面
        if neg_count > pos_count and neg_count >= 2:
            return min(0.4, base_score - 0.15)
        
        # 5. 没有明显情感词 -> 信任SnowNLP但偏向中性偏正
        if base_score > 0.6:
            return 0.7  # 官方新闻默认偏正面
        elif base_score < 0.4:
            return 0.45  # 不太可能是负面
        else:
            return 0.55  # 中性偏正
            
    except:
        return 0.55  # 异常时返回中性偏正

NEGATIVE_KEYWORDS = {
    '事故', '灾难', '火灾', '爆炸', '伤亡', '死亡', '受伤',
    '犯罪', '诈骗', '贪污', '腐败', '违法', '违规',
    '投诉', '举报', '质疑', '争议', '纠纷', '冲突',
    '失败', '亏损', '下跌', '下降', '减少', '降低', '恶化',
    '批评', '谴责', '处罚', '制裁', '禁止', '限制', '取缔',
    '污染', '破坏', '损害', '损失', '漏洞', '缺陷',
    '不满', '反对', '抵制', '抗议',
}

POSITIVE_KEYWORDS = {
    '成功', '成就', '突破', '创新', '发展', '进步', '提升',
    '优秀', '良好', '优异', '卓越', '突出', '显著',
    '增长', '增加', '上升', '改善', '优化', '完善',
    '合作', '共赢', '友好', '和谐', '稳定', '安全', '保障',
    '支持', '帮助', '援助', '促进', '推动', '助力',
    '庆祝', '祝贺', '表彰', '奖励', '荣誉', '赞扬', '肯定',
}

def get_sentiment_info(score):
    """获取情感信息"""
    if score > 0.6:
        return "positive", "😊 正面", "#2ca02c"
    elif score < 0.4:
        return "negative", "😟 负面", "#d62728"
    else:
        return "neutral", "😐 中性", "#ff7f0e"

# ==================== 词云生成 ====================
def generate_wordcloud_from_titles(titles, mask_file='guangdong_mask.png'):
    """从标题列表生成词云（广东地图形状）"""
    if not titles or len(titles) == 0:
        return None
    
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
    
    word_freq = Counter(all_words)
    
    # 加载广东地图mask
    mask = None
    
    if os.path.exists(mask_file):
        try:
            from PIL import Image
            import numpy as np
            mask_img = Image.open(mask_file).convert('L')
            mask = np.array(mask_img)
            mask_height, mask_width = mask.shape
            print(f"✅ 加载mask成功: {mask_width}x{mask_height}")
        except Exception as e:
            print(f"️ 加载mask失败: {e}，使用矩形词云")
            mask_width, mask_height = 640, 480
    else:
        mask_width, mask_height = 640, 480
    
    # 生成词云（使用mask的实际尺寸）
    wc = WordCloud(
        font_path='C:/Windows/Fonts/msyh.ttc',
        width=mask_width,
        height=mask_height,
        background_color='white',
        max_words=100,
        colormap='viridis',
        mask=mask,
        contour_width=0,  # 不显示边框
        contour_color='steelblue'
    )
    
    wc.generate_from_frequencies(word_freq)
    
    img = wc.to_image()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()

# ==================== 热点关键词提取 ====================
def extract_hot_topics_from_titles(titles, top_n=20):
    """从标题提取热点关键词"""
    if not titles or len(titles) == 0:
        return []
    
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
    
    word_counts = Counter(all_words)
    max_freq = max(word_counts.values())
    min_threshold = max(8, max_freq * 0.5)
    
    filtered = [(word, freq) for word, freq in word_counts.most_common() if freq >= min_threshold]
    
    return filtered[:top_n]

# ==================== 显示函数 ====================
def display_metric_simple(value, label, value_type="default"):
    """显示简单指标（使用Streamlit原生metric，样式统一）"""
    st.metric(label=label, value=value)

def display_news_card(title, date, score, content):
    """显示新闻卡片（带情感颜色边框和emoji）"""
    cat, label, color = get_sentiment_info(score)
    
    # 使用HTML创建带彩色边框的卡片
    card_html = f"""
    <div style="
        border-left: 6px solid {color};
        background: linear-gradient(90deg, {color}10 0%, white 100%);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        cursor: pointer;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #2c3e50; flex: 1;">{title[:60]}{'...' if len(title)>60 else ''}</span>
            <span style="background:{color}; color:white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; margin-left: 1rem; white-space: nowrap;">{label}</span>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # 使用expander展开正文
    with st.expander("📖 查看正文"):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"""
            <div style="
                background:{color};
                color:white;
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            ">
                <div style="font-size: 2rem; font-weight: bold;">{score:.3f}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem;">{label}</div>
                <div style="font-size: 0.85rem; margin-top: 0.3rem; opacity: 0.9;">{date}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.write(content)

# ==================== 图表函数 ====================
def create_line_chart(df, x_col, y_col, title, xlabel, ylabel):
    """创建折线图"""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=8)
    # 去除emoji，增大字体
    clean_title = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', title)
    ax.set_title(clean_title.strip(), fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def create_pie_chart(data, title):
    """创建饼图"""
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#2ca02c', '#ff7f0e', '#d62728']
    wedges, texts, autotexts = ax.pie(
        data.values, 
        labels=data.index, 
        autopct='%1.1f%%', 
        colors=colors, 
        startangle=90,
        textprops={'fontsize': 12}
    )
    # 增大标题字体
    clean_title = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', title)
    ax.set_title(clean_title.strip(), fontsize=16, fontweight='bold', pad=20)
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
        st.info("⏳ 正在计算情感分析（这可能需要几分钟）...")
        sentiments = []
        total = len(df)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, row in df.iterrows():
            score = calculate_sentiment_v2(row.get('content', ''), row.get('title', ''))
            sentiments.append(score)
            
            # 每100条更新一次进度
            if (idx + 1) % 100 == 0:
                progress = (idx + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"处理进度: {idx + 1}/{total} ({progress*100:.1f}%)")
        
        df['sentiment'] = sentiments
        progress_bar.progress(1.0)
        status_text.text("✅ 情感分析完成！")
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
    
    # 5个指标（无卡片样式，只有文字）
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_simple(f"{len(df):,}", " 新闻总数")
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
    
    # 月度趋势
    st.markdown('<div class="subsection-title">📊 月度趋势分析</div>', unsafe_allow_html=True)
    
    monthly = df.groupby('year_month').agg({
        'title': 'count',
        'sentiment': 'mean'
    }).rename(columns={'title': 'count', 'sentiment': 'avg_sent'})
    monthly = monthly.reset_index()
    monthly['year_month'] = monthly['year_month'].astype(str)
    
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
        fig2 = create_line_chart(monthly, 'year_month', 'avg_sent', '💭 月度平均情感趋势', '月份', '得分')
        st.pyplot(fig2)
    
    col3, col4 = st.columns(2)
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
        labels = {'positive': '正面', 'neutral': '中性', 'negative': ' 负面'}
        sentiment_dist.index = [labels.get(c, c) for c in sentiment_dist.index]
        fig5 = create_pie_chart(sentiment_dist, '总体情感分布')
        st.pyplot(fig5)
        
    with col2:
        st.markdown('<div class="subsection-title">️ 全部新闻词云</div>', unsafe_allow_html=True)
        # 使用真实的广东省轮廓
        wordcloud_img = generate_wordcloud_from_titles(df['title'].tolist(), mask_file='guangdong_true_mask.png')
        if wordcloud_img:
            # 与饼图等高对齐（饼图figsize=(8,6)约480px高）
            st.image(wordcloud_img, width=480)
        else:
            st.info("暂无词云数据")
        
    # 总体热点关键词
    st.markdown('<div class="subsection-title"> 总体热点关键词 TOP 20</div>', unsafe_allow_html=True)
        
    hot_topics = extract_hot_topics_from_titles(df['title'].tolist(), top_n=20)
    if hot_topics:
        hot_df = pd.DataFrame(hot_topics, columns=['关键词', '出现次数'])
        hot_df.insert(0, '排名', range(1, len(hot_df) + 1))
        # 添加居中样式
        st.markdown("""
        <style>
        div[data-testid="stDataFrame"] {
            text-align: center !important;
        }
        </style>
        """, unsafe_allow_html=True)
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
    st.markdown(f'<div class="subsection-title"> {selected} 月度概览</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        display_metric_simple(f"{len(month_df):,}", " 本月新闻总数")
    with col2:
        avg = month_df['sentiment'].mean()
        cat, label, _ = get_sentiment_info(avg)
        display_metric_simple(f"{avg:.3f}", f" 平均情感 ({label})", cat)
    with col3:
        pos = len(month_df[month_df['sentiment_category'] == 'positive'])
        display_metric_simple(f"{pos:,}", " 正面新闻", "positive")
    with col4:
        neg = len(month_df[month_df['sentiment_category'] == 'negative'])
        display_metric_simple(f"{neg:,}", " 负面新闻", "negative")
    with col5:
        neu = len(month_df[month_df['sentiment_category'] == 'neutral'])
        display_metric_simple(f"{neu:,}", " 中性新闻", "neutral")
    
    # 本月词云 + 热点关键词
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="subsection-title">️ 本月词云</div>', unsafe_allow_html=True)
        wordcloud_img = generate_wordcloud_from_titles(month_df['title'].tolist(), mask_file='guangdong_true_mask.png')
        if wordcloud_img:
            # 与表格等高对齐
            st.image(wordcloud_img, width=480)
        else:
            st.info("暂无词云数据")
    
    with col2:
        st.markdown('<div class="subsection-title"> 本月热点关键词 TOP 10</div>', unsafe_allow_html=True)
        
        hot_file = 'monthly_hot_topics.csv'
        if os.path.exists(hot_file):
            try:
                hot_df = pd.read_csv(hot_file, encoding='utf-8-sig')
                month_hot = hot_df[hot_df['month'] == selected].sort_values('rank').head(10)
                
                if len(month_hot) > 0:
                    display_df = month_hot[['rank', 'word', 'frequency']].rename(
                        columns={'rank': '排名', 'word': '关键词', 'frequency': '频次'}
                    )
                    # 添加居中样式
                    st.markdown("""
                    <style>
                    div[data-testid="stDataFrame"] {
                        text-align: center !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"{selected} 暂无热点关键词")
            except Exception as e:
                st.warning(f"读取失败: {e}")
        else:
            hot_topics = extract_hot_topics_from_titles(month_df['title'].tolist(), top_n=10)
            if hot_topics:
                hot_df = pd.DataFrame(hot_topics, columns=['关键词', '频次'])
                hot_df.insert(0, '排名', range(1, len(hot_df) + 1))
                # 添加居中样式
                st.markdown("""
                <style>
                div[data-testid="stDataFrame"] {
                    text-align: center !important;
                }
                </style>
                """, unsafe_allow_html=True)
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
    st.markdown('<div class="main-title">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)
    
    df = load_data()
    if df is None:
        return
    
    st.sidebar.title("📋 导航菜单")
    page = st.sidebar.radio("选择页面", [" 全局概览", "📅 月度详情"])
    
    if page == " 全局概览":
        show_overview(df)
    else:
        show_monthly(df)

if __name__ == "__main__":
    main()
