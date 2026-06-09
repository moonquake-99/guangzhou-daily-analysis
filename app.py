"""
广州日报舆情分析系统 - Streamlit Web应用
功能：数据展示、情感分析、热点追踪、词云可视化、新闻搜索

依赖库安装：
pip install streamlit pandas matplotlib wordcloud jieba snownlp requests beautifulsoup4 numpy pillow

运行方式：
streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import subprocess
from datetime import datetime
from collections import Counter
import jieba
from snownlp import SnowNLP
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from PIL import Image
import io
import base64

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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


# ==================== 停用词表（复用 extract_hot_topics.py）====================
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

MEDIA_WORDS = {
    '记者', '本报', '编辑', '通讯员', '广州日报', '日报',
    '南方日报', '信息时报', '新快报', '羊城晚报', '南方都市报',
    '澎湃新闻', '新华社', '人民日报', '央视新闻', '凤凰卫视',
    '新浪网', '腾讯网', '网易', '搜狐', '今日头条',
    '公众号', '微信', '微博', '抖音', '快手',
    '报道', '采访', '新闻', '消息', '快讯', '直播',
    '主播', '主持人', '评论员', '特约', '专栏',
}

LEADER_NAMES = {
    '习近平', '李克强', '李强', '汪洋', '王沪宁',
    '赵乐际', '韩正', '丁薛祥', '陈希', '胡春华',
    '刘鹤', '孙春兰', '杨洁篪', '郭声琨', '黄坤明',
    '蔡奇', '王毅', '肖捷', '郑建邦', '何立峰',
    '王小洪', '吴政隆', '谌贻琴', '总书记', '总理', '主席'
}

GENERIC_WORDS = {
    '建设', '推动', '发展', '提高', '加强', '促进', '开展',
    '进行', '实现', '坚持', '努力', '推进', '落实', '做好',
    '完成', '实施', '执行', '组织', '安排', '部署',
    '要求', '强调', '指出', '提出', '表示', '认为', '说明',
    '介绍', '了解', '据悉', '通报', '发布', '公布',
    '举行', '召开', '开幕', '闭幕', '启动', '举办',
    '参加', '出席', '莅临', '座谈', '调研', '考察',
    '会见', '接见', '慰问', '祝贺', '庆祝',
    '关于', '贯彻', '学习', '精神', '公告', '通知',
    '决定', '意见', '方案', '规划', '计划', '总结',
    '报告', '讲话', '发言', '致辞', '指示',
    '积极', '重要', '主要', '良好', '广大', '全面', '深入',
    '持续', '进一步', '不断', '加快', '大力', '认真',
    '切实', '有效', '显著', '突出', '明显', '稳步',
    '群众', '市民', '人们', '我们', '他们', '大家', '各位',
    '这个', '那个', '这些', '那些', '其中', '上述', '以下',
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
    '一带一路', '自贸区', '保税区', '开发区',
]

for word in CUSTOM_WORDS:
    jieba.add_word(word)


# ==================== 工具函数 ====================

def get_chinese_font():
    """自动检测Windows系统中可用的中文字体"""
    if os.name == 'nt':  # Windows
        font_paths = [
            r'C:\Windows\Fonts\msyh.ttc',      # Microsoft YaHei
            r'C:\Windows\Fonts\simhei.ttf',     # SimHei
            r'C:\Windows\Fonts\simsun.ttc',     # SimSun
        ]
        for path in font_paths:
            if os.path.exists(path):
                return path
    return None  # 使用默认字体


@st.cache_data(ttl=3600)
def load_data():
    """加载CSV数据，如果sentiment列不存在则计算并缓存"""
    csv_file = 'news_with_keywords.csv'
    
    if not os.path.exists(csv_file):
        st.error(f"❌ 找不到数据文件: {csv_file}")
        return None
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        # 检查是否有sentiment列，如果没有则计算
        if 'sentiment' not in df.columns:
            st.info("⏳ 首次加载，正在计算情感分析...（这可能需要几分钟）")
            df = calculate_and_add_sentiment(df)
        
        # 确保date列是datetime类型
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['month'] = df['date'].dt.strftime('%Y-%m')
        
        return df
    
    except Exception as e:
        st.error(f"❌ 加载数据失败: {e}")
        return None


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


def calculate_sentiment_batch(contents, titles=None):
    """批量计算情感得分"""
    sentiments = []
    for i, content in enumerate(contents):
        title = titles[i] if titles and i < len(titles) else ''
        score = calculate_sentiment_with_keywords(content, title)
        sentiments.append(score)
    return sentiments


def calculate_and_add_sentiment(df):
    """为DataFrame添加情感得分列，并保存到CSV"""
    with st.spinner('正在计算情感分析...'):
        # 先计算前5条作为示例展示
        st.info("📊 情感分析示例（前5条新闻）：")
        sample_indices = range(min(5, len(df)))
        
        example_data = []
        for idx in sample_indices:
            content = df.iloc[idx]['content']
            title = df.iloc[idx]['title']
            
            # 使用改进的情感分析方法
            score = calculate_sentiment_with_keywords(content, title)
            
            if score > 0.6:
                category = "✅ 正面"
                emoji = "😊"
            elif score < 0.4:
                category = "❌ 负面"
                emoji = "😟"
            else:
                category = "➖ 中性"
                emoji = "😐"
            
            example_data.append({
                '标题': title[:50] + '...' if len(title) > 50 else title,
                '情感得分': f"{score:.4f}",
                '情感类别': f"{emoji} {category}"
            })
        
        # 显示示例表格
        example_df = pd.DataFrame(example_data)
        st.table(example_df)
        
        st.info("⏳ 正在计算剩余新闻的情感分析...")
        
        # 批量计算所有情感得分（传入标题）
        sentiments = calculate_sentiment_batch(df['content'].tolist(), df['title'].tolist())
        df['sentiment'] = sentiments
        
        # 保存到CSV
        try:
            df.to_csv('news_with_keywords.csv', index=False, encoding='utf-8-sig')
            st.success("✅ 情感分析计算完成并已保存！")
        except Exception as e:
            st.warning(f"⚠️ 保存失败: {e}，但将继续运行")
    
    return df


def filter_word(word):
    """判断一个词是否应该被过滤"""
    if len(word) < 2:
        return True
    if word in ALL_STOPWORDS:
        return True
    if word.isdigit():
        return True
    if re.match(r'^[\W_]+$', word):
        return True
    return False


def extract_keywords_from_titles(titles, top_n=15):
    """从标题列表中提取关键词"""
    all_words = []
    for title in titles:
        if isinstance(title, str) and title.strip():
            words = jieba.cut(title)
            for word in words:
                word = word.strip()
                if word and not filter_word(word):
                    all_words.append(word)
    
    word_counts = Counter(all_words)
    return word_counts.most_common(top_n)


def extract_hot_topics(df, selected_month, top_n=10):
    """提取月度热点话题（复用extract_hot_topics.py的逻辑）"""
    month_df = df[df['month'] == selected_month]
    
    if month_df.empty:
        return []
    
    # 从标题提取关键词
    all_words = []
    for title in month_df['title'].dropna():
        words = jieba.cut(title)
        for word in words:
            word = word.strip()
            if word and not filter_word(word):
                all_words.append(word)
    
    word_counts = Counter(all_words)
    return word_counts.most_common(top_n)


# ==================== 可视化函数 ====================

def plot_monthly_trend(df):
    """绘制月度新闻数量趋势图"""
    monthly_counts = df.groupby('month').size().reset_index(name='count')
    monthly_counts = monthly_counts.sort_values('month')
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(monthly_counts['month'], monthly_counts['count'], color='#1f77b4', alpha=0.7)
    ax.plot(monthly_counts['month'], monthly_counts['count'], color='#d62728', marker='o', linewidth=2)
    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('新闻数量', fontsize=12)
    ax.set_title('月度新闻发布数量趋势', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)


def plot_sentiment_pie(df):
    """绘制总体情感分布饼图"""
    def categorize_sentiment(score):
        if score > 0.6:
            return '正面'
        elif score < 0.4:
            return '负面'
        else:
            return '中性'
    
    df['sentiment_category'] = df['sentiment'].apply(categorize_sentiment)
    category_counts = df['sentiment_category'].value_counts()
    
    colors = ['#2ca02c', '#ff7f0e', '#d62728']  # 绿、橙、红
    labels = [f'{cat} ({count})' for cat, count in category_counts.items()]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        category_counts.values,
        labels=labels,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 12}
    )
    ax.set_title('总体情感分布', fontsize=14, fontweight='bold')
    
    st.pyplot(fig)


def plot_sentiment_trend(df):
    """绘制月度情感趋势图"""
    monthly_sentiment = df.groupby('month')['sentiment'].mean().reset_index()
    monthly_sentiment = monthly_sentiment.sort_values('month')
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly_sentiment['month'], monthly_sentiment['sentiment'], 
            color='#2ca02c', marker='o', linewidth=2, markersize=8)
    ax.fill_between(range(len(monthly_sentiment)), 
                    monthly_sentiment['sentiment'], 
                    alpha=0.3, color='#2ca02c')
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='中性线')
    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('平均情感得分', fontsize=12)
    ax.set_title('月度情感趋势分析', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)


def plot_keyword_bar(df, selected_month):
    """绘制月度关键词条形图"""
    month_df = df[df['month'] == selected_month]
    if month_df.empty:
        st.warning("该月没有数据")
        return
    
    keywords = extract_keywords_from_titles(month_df['title'].tolist(), top_n=15)
    
    if not keywords:
        st.warning("未提取到关键词")
        return
    
    words, freqs = zip(*keywords)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(words))
    bars = ax.barh(y_pos, freqs, color='#2ca02c', alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(words, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel('频次', fontsize=12)
    ax.set_title(f'{selected_month} 月热点关键词 Top 15', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # 在柱状图上显示数值
    for i, (word, freq) in enumerate(keywords):
        ax.text(freq + 0.5, i, str(freq), va='center', fontsize=10)
    
    plt.tight_layout()
    st.pyplot(fig)


@st.cache_data
def generate_wordcloud_image(text, font_path=None):
    """生成词云图片"""
    if not text or not text.strip():
        return None
    
    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=400,
        background_color='white',
        max_words=100,
        colormap='viridis',
        contour_width=1,
        contour_color='steelblue'
    ).generate(text)
    
    return wc.to_image()


def display_wordcloud(df, selected_month, font_path):
    """显示词云：整体 + 单月"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("☁️ 整体词云（所有月份）")
        all_titles = ' '.join(df['title'].dropna())
        wc_all = generate_wordcloud_image(all_titles, font_path)
        if wc_all:
            st.image(wc_all, use_container_width=True)
    
    with col2:
        st.subheader(f"☁️ {selected_month} 月词云")
        month_df = df[df['month'] == selected_month]
        if not month_df.empty:
            month_titles = ' '.join(month_df['title'].dropna())
            wc_month = generate_wordcloud_image(month_titles, font_path)
            if wc_month:
                st.image(wc_month, use_container_width=True)
        else:
            st.warning("该月没有数据")


def display_negative_news(df, selected_month):
    """展示负面新闻预警"""
    month_df = df[df['month'] == selected_month].copy()
    
    if month_df.empty:
        st.warning("该月没有数据")
        return
    
    # 按情感得分升序排列，取前3条
    negative_top3 = month_df.nsmallest(3, 'sentiment')
    
    for idx, row in negative_top3.iterrows():
        sentiment_score = row['sentiment']
        
        # 根据情感得分设置颜色
        if sentiment_score < 0.3:
            emoji = "🔴"
        elif sentiment_score < 0.4:
            emoji = "🟠"
        else:
            emoji = "🟡"
        
        with st.expander(f"{emoji} {row['title']} (情感得分: {sentiment_score:.3f})"):
            st.markdown(f"**发布日期**: {row['date'].strftime('%Y-%m-%d')}")
            st.markdown(f"**情感得分**: {sentiment_score:.3f}")
            st.markdown("---")
            st.write(row['content'])


def display_news_detail(df, selected_month):
    """展示选中月份的新闻列表（可展开查看详情）"""
    month_df = df[df['month'] == selected_month].copy()
    
    if month_df.empty:
        st.warning("该月没有数据")
        return
    
    # 按日期降序排列
    month_df = month_df.sort_values('date', ascending=False)
    
    # 显示前20条新闻
    display_count = min(20, len(month_df))
    st.info(f"显示最近 {display_count} 条新闻（共 {len(month_df)} 条）")
    
    for idx, row in month_df.head(display_count).iterrows():
        sentiment_score = row['sentiment']
        
        # 根据情感得分设置图标
        if sentiment_score > 0.6:
            emoji = "😊"
        elif sentiment_score < 0.4:
            emoji = "😟"
        else:
            emoji = "😐"
        
        with st.expander(f"{emoji} {row['title']} ({row['date'].strftime('%Y-%m-%d')})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**情感得分**: {sentiment_score:.3f}")
                if 'reporter' in row.index and pd.notna(row['reporter']):
                    st.markdown(f"**记者**: {row['reporter']}")
            with col2:
                if sentiment_score > 0.6:
                    st.success("正面")
                elif sentiment_score < 0.4:
                    st.error("负面")
                else:
                    st.warning("中性")
            
            st.markdown("---")
            st.write(row['content'])
            
            if 'url' in row.index and pd.notna(row['url']):
                st.markdown(f"[🔗 阅读原文]({row['url']})")


def export_data(df, selected_month):
    """导出数据功能"""
    st.markdown("### 📥 数据导出")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 导出当前月份数据", use_container_width=True):
            month_df = df[df['month'] == selected_month]
            if not month_df.empty:
                csv = month_df.to_csv(index=False, encoding='utf-8-sig')
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="news_{selected_month}.csv">点击下载 CSV 文件</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success(f"✅ 已生成 {selected_month} 月数据文件")
            else:
                st.warning("该月没有数据")
    
    with col2:
        if st.button("🌍 导出全部数据", use_container_width=True):
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="news_all.csv">点击下载 CSV 文件</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("✅ 已生成全部数据文件")


def search_and_display_news(df, keyword):
    """搜索并展示新闻"""
    if not keyword:
        return
    
    # 搜索标题包含关键词的新闻
    mask = df['title'].str.contains(keyword, case=False, na=False)
    results = df[mask]
    
    if results.empty:
        st.info(f"未找到包含 '{keyword}' 的新闻")
        return
    
    st.success(f"找到 {len(results)} 条相关新闻")
    
    # 按日期降序排列
    results = results.sort_values('date', ascending=False)
    
    for idx, row in results.head(20).iterrows():  # 最多显示20条
        sentiment_score = row['sentiment']
        
        # 根据情感得分设置图标
        if sentiment_score > 0.6:
            emoji = "😊"
        elif sentiment_score < 0.4:
            emoji = "😟"
        else:
            emoji = "😐"
        
        with st.expander(f"{emoji} {row['title']} ({row['date'].strftime('%Y-%m-%d')})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**情感得分**: {sentiment_score:.3f}")
            with col2:
                if sentiment_score > 0.6:
                    st.success("正面")
                elif sentiment_score < 0.4:
                    st.error("负面")
                else:
                    st.warning("中性")
            
            st.markdown("---")
            st.write(row['content'])
            
            if 'url' in row.index and pd.notna(row['url']):
                st.markdown(f"[🔗 阅读原文]({row['url']})")


# ==================== 数据更新功能 ====================

def update_data_from_website():
    """从官网更新数据（调用爬虫脚本）"""
    st.info("🔄 正在从官网获取最新数据...")
    
    try:
        # 运行爬虫脚本
        result = subprocess.run(
            ['python', 'gzdaily_spider.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            st.success("✅ 爬虫运行成功！正在重新加载数据...")
            
            # 这里需要添加JSON合并到CSV的逻辑
            # 简化版：提示用户手动运行extract_news_from_json.py和data_cleaning.py
            st.warning("⚠️ 请手动运行以下步骤以更新CSV文件：")
            st.code("1. python extract_news_from_json.py\n2. python data_cleaning.py\n3. python extract_keywords_for_each_news.py")
            st.info("完成后刷新页面即可看到最新数据")
        else:
            st.error(f"❌ 爬虫运行失败:\n{result.stderr}")
    
    except subprocess.TimeoutExpired:
        st.error("⏰ 爬虫运行超时，请稍后重试")
    except Exception as e:
        st.error(f"❌ 更新失败: {e}")


# ==================== 主程序 ====================

def main():
    # 标题
    st.markdown('<div class="main-header">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)
    
    # 加载数据
    df = load_data()
    if df is None:
        st.stop()
    
    # 获取可用月份列表
    available_months = sorted(df['month'].unique(), reverse=True)
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        # 数据更新按钮
        st.markdown("**📥 数据管理**")
        if st.button("🔄 从官网更新数据", use_container_width=True):
            update_data_from_website()
        
        st.divider()
        
        # 月份选择
        st.markdown("**📅 月份筛选**")
        selected_month = st.selectbox(
            "选择要分析的月份",
            options=available_months,
            index=0,
            help="选择月份后，右侧将显示该月的详细分析"
        )
        
        st.divider()
        
        # 搜索框
        st.markdown("**🔍 新闻搜索**")
        search_keyword = st.text_input(
            "输入关键词搜索新闻",
            placeholder="例如：经济、科技、文化...",
            help="搜索标题中包含该关键词的新闻"
        )
        
        st.divider()
        
        # 数据统计
        st.markdown("**📊 数据概览**")
        st.metric("总新闻数", len(df))
        st.metric("月份数", len(available_months))
        avg_sentiment = df['sentiment'].mean()
        st.metric("平均情感得分", f"{avg_sentiment:.3f}")
    
    # ==================== 主区域 ====================
    
    # --- 选中月份信息区 ---
    st.markdown(f'<div class="section-header">📊 {selected_month} 月数据分析</div>', unsafe_allow_html=True)
    
    month_df = df[df['month'] == selected_month]
    
    # 指标卡
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        news_count = len(month_df)
        st.metric("📰 新闻数量", news_count)
    
    with col2:
        avg_sent = month_df['sentiment'].mean() if not month_df.empty else 0
        st.metric("😊 平均情感得分", f"{avg_sent:.3f}")
    
    with col3:
        positive_count = len(month_df[month_df['sentiment'] > 0.6])
        st.metric("✅ 正面新闻", positive_count)
    
    with col4:
        negative_count = len(month_df[month_df['sentiment'] < 0.4])
        st.metric("❌ 负面新闻", negative_count)
    
    st.divider()
    
    # 热点话题 Top 10
    st.markdown("### 🔥 本月热点话题 Top 10")
    hot_topics = extract_hot_topics(df, selected_month, top_n=10)
    if hot_topics:
        topics_df = pd.DataFrame(hot_topics, columns=['关键词', '频次'])
        st.table(topics_df)
    else:
        st.warning("未提取到热点话题")
    
    st.divider()
    
    # 词云
    font_path = get_chinese_font()
    display_wordcloud(df, selected_month, font_path)
    
    st.divider()
    
    # 关键词条形图
    st.markdown("### 🔑 本月热点关键词")
    plot_keyword_bar(df, selected_month)
    
    st.divider()
    
    # 负面新闻预警
    st.markdown("### ⚠️ 负面新闻预警（情感得分最低的3条）")
    display_negative_news(df, selected_month)
    
    st.divider()
    
    # 新闻详情
    st.markdown("### 📋 新闻详情（最近20条）")
    display_news_detail(df, selected_month)
    
    # ==================== 全局功能区 ====================
    st.divider()
    st.markdown('<div class="section-header">🌍 全局数据分析</div>', unsafe_allow_html=True)
    
    # 总体情感饼图
    st.markdown("### 😊 总体情感分布")
    plot_sentiment_pie(df)
    
    st.divider()
    
    # 月度趋势图
    st.markdown("### 📈 月度新闻数量趋势")
    plot_monthly_trend(df)
    
    st.divider()
    
    # 情感趋势分析
    st.markdown("### 📉 月度情感趋势分析")
    plot_sentiment_trend(df)
    
    st.divider()
    
    # 数据导出
    export_data(df, selected_month)
    
    st.divider()
    
    # 新闻搜索
    if search_keyword:
        st.markdown(f"### 🔍 搜索结果: '{search_keyword}'")
        search_and_display_news(df, search_keyword)


if __name__ == '__main__':
    main()
