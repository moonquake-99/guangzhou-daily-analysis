"""
广州日报舆情分析系统 - 政府网站风格优化版 (Linux兼容版)
修复版 - 修正导航菜单和页面路由错误
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
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud
import io
import platform

# ==================== 跨平台中文字体配置 ====================
def setup_chinese_font():
    """设置跨平台中文字体"""
    system = platform.system()
    font_found = False
    
    if system == 'Windows':
        # Windows字体路径（使用原始字符串避免转义问题）
        font_candidates = [
            r'C:\Windows\Fonts\msyh.ttc',  # 微软雅黑
            r'C:\Windows\Fonts\simhei.ttf',  # 黑体
            r'C:\Windows\Fonts\simsun.ttc',  # 宋体
            'C:/Windows/Fonts/msyh.ttc',  # 备用路径
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/simsun.ttc',
        ]
    elif system == 'Darwin':  # macOS
        font_candidates = [
            '/System/Library/Fonts/PingFang.ttc',  # 苹方
            '/Library/Fonts/Arial Unicode.ttf',
        ]
    else:  # Linux (包括Codespaces)
        font_candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # 文泉驿微米黑
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]
    
    for font_path in font_candidates:
        if os.path.exists(font_path):
            # 设置字体
            matplotlib.rcParams['font.sans-serif'] = [font_path]
            matplotlib.rcParams['axes.unicode_minus'] = False
            print(f"✅ Matplotlib使用字体: {font_path}")
            font_found = True
            break
    
    if not font_found:
        print("⚠️ 未找到中文字体，图表可能显示方框")
        if system == 'Linux':
            print("💡 解决方案: 在Codespace终端执行以下命令安装字体:")
            print("   sudo apt-get update && sudo apt-get install -y fonts-wqy-zenhei")
        # 使用默认字体
        matplotlib.rcParams['font.sans-serif'] = ['sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False

# 初始化字体配置
setup_chinese_font()

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="广州日报舆情分析系统",
    page_icon="",
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
        color: #C41E3A;
        margin: 1rem 0;
        padding: 1rem;
        border-bottom: 3px solid #C41E3A;
        background: linear-gradient(to right, #FFF8DC, #FFFFFF, #FFF8DC);
    }
    
    /* 段落标题 - 政府网站风格 */
    .section-title {
        font-size: 1.6rem;
        font-weight: bold;
        color: #C41E3A;
        margin: 1.5rem 0 1rem 0;
        padding: 0.5rem 1rem;
        border-left: 5px solid #C41E3A;
        background: linear-gradient(to right, #FFF8DC, #FFFFFF);
    }
    
    .subsection-title {
        font-size: 1.6rem;
        font-weight: bold;
        color: #C41E3A;
        margin: 1rem 0 0.8rem 0;
        padding: 0.5rem 1rem;
        border-left: 5px solid #C41E3A;
        background: linear-gradient(to right, #FFF8DC, #FFFFFF);
    }
    
    /* 指标数值样式 */
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #C41E3A;
        margin-bottom: 0.3rem;
    }
    
    .metric-value-positive {
        color: #2ca02c !important;
    }
    
    .metric-value-negative {
        color: #d62728 !important;
    }
    
    .metric-value-neutral {
        color: #B8860B !important;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        font-weight: 500;
    }
    
    /* 指标卡片 - 政府网站风格 */
    .metric-card {
        background: linear-gradient(135deg, #FFF8DC 0%, #FFFFFF 100%);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 3px 10px rgba(196, 30, 58, 0.15);
        margin: 0.5rem;
        border-left: 6px solid #C41E3A;
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
        border-left: 5px solid #C41E3A;
        transition: all 0.3s;
    }
    
    .news-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(196, 30, 58, 0.2);
    }
    
    .news-card-positive {
        border-left-color: #2ca02c !important;
        background: linear-gradient(90deg, rgba(44,160,44,0.08) 0%, white 100%);
    }
    
    .news-card-negative {
        border-left-color: #d62728 !important;
        background: linear-gradient(90deg, rgba(214,39,40,0.08) 0%, white 100%);
    }
    
    .news-card-neutral {
        border-left-color: #DAA520 !important;
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
        background: linear-gradient(135deg, #2ca02c 0%, #228B22 100%);
    }
    
    .sentiment-negative {
        background: linear-gradient(135deg, #d62728 0%, #C41E3A 100%);
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, #DAA520 0%, #B8860B 100%);
    }
    
    /* 表格样式优化 */
    div[data-testid="stDataFrame"] table {
        border-collapse: collapse;
    }
    
    div[data-testid="stDataFrame"] th {
        background: linear-gradient(135deg, #C41E3A 0%, #8B4513 100%) !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 0.8rem !important;
    }
    
    div[data-testid="stDataFrame"] td {
        text-align: center !important;
        padding: 0.6rem !important;
        border-bottom: 1px solid #E0E0E0 !important;
    }
    
    div[data-testid="stDataFrame"] tr:nth-child(even) {
        background-color: #FFF8DC !important;
    }
    
    div[data-testid="stDataFrame"] tr:hover {
        background-color: #FFE4E1 !important;
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
    '大湾区', '粤港澳大湾区', '前海', '横琴', '南沙',
    '高质量发展', '数字经济', '人工智能', 'AI', '大模型',
    '乡村振兴', '共同富裕', '碳中和', '碳达峰', '双碳',
]

for word in CUSTOM_WORDS:
    jieba.add_word(word)

# ==================== 情感分析函数 ====================
def calculate_sentiment_v2(content, title=''):
    """计算情感分数（优化版）"""
    text = (title + ' ' + content)[:500]
    
    if not text.strip():
        return 0.5
    
    try:
        s = SnowNLP(text)
        base_score = s.sentiments
    except:
        base_score = 0.5
    
    # 关键词调整
    text_lower = text.lower()
    
    negative_count = 0
    positive_count = 0
    
    for word in NEGATIVE_KEYWORDS:
        if word in text_lower:
            negative_count += 1
    
    for word in POSITIVE_KEYWORDS:
        if word in text_lower:
            positive_count += 1
    
    if negative_count > positive_count:
        base_score = base_score * 0.7
    elif positive_count > negative_count:
        base_score = base_score * 0.3 + 0.7
    
    return max(0.0, min(1.0, base_score))

# ==================== 情感分类 ====================
NEGATIVE_KEYWORDS = {
    '危机', '灾难', '事故', '问题', '困难', '挑战',
    '下降', '减少', '降低', '恶化', '衰退', '萧条',
    '冲突', '矛盾', '争议', '纠纷', '诉讼', '违法',
    '批评', '指责', '谴责', '不满', '反对', '抵制',
    '失败', '损失', '亏损', '倒闭', '破产', '裁员',
    '污染', '破坏', '违规', '违规', '造假', '欺诈',
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
        return "positive", "正面", "#2ca02c"
    elif score < 0.4:
        return "negative", "负面", "#d62728"
    else:
        return "neutral", "中性", "#B8860B"

# ==================== 词云生成（跨平台字体支持）====================
def generate_wordcloud_from_titles(titles, mask_file='guangdong_true_mask.png'):
    """从标题列表生成词云（广东地图形状，政府网站配色）"""
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
            print(f"⚠️ 加载mask失败: {e}，使用矩形词云")
            mask_width, mask_height = 640, 480
    else:
        mask_width, mask_height = 640, 480
    
    # 自定义颜色函数（政府网站配色）
    def government_colors(word, font_size, position, orientation, random_state, font_path=None):
        """政府网站配色方案"""
        import random
        r = random.Random()
        r.seed(hash(position))
        
        colors = [
            '#C41E3A',  # 中国红
            '#8B4513',  # 金棕色
            '#DAA520',  # 金色
            '#B8860B',  # 暗金色
            '#228B22',  # 深绿色
        ]
        return r.choice(colors)
    
    # 根据操作系统选择中文字体
    system = platform.system()
    
    if system == 'Windows':
        font_candidates = [
            'C:/Windows/Fonts/msyh.ttc',  # Windows: 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
        ]
        font_path = None
        for candidate in font_candidates:
            if os.path.exists(candidate):
                font_path = candidate
                print(f"✅ 找到Windows字体: {font_path}")
                break
        if not font_path:
            print("⚠️ Windows未找到中文字体，使用默认字体")
    elif system == 'Darwin':  # macOS
        font_candidates = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS: 苹方
            '/Library/Fonts/Arial Unicode.ttf',
        ]
        font_path = None
        for candidate in font_candidates:
            if os.path.exists(candidate):
                font_path = candidate
                print(f"✅ 找到macOS字体: {font_path}")
                break
        if not font_path:
            print("⚠️ macOS未找到中文字体，使用默认字体")
    else:  # Linux (包括Codespaces)
        # Linux系统尝试使用常见中文字体
        font_candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # 文泉驿微米黑
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
            '/usr/share/fonts/TTF/DejaVuSans.ttf',  # DejaVu Sans
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            None  # 最后尝试默认字体
        ]
        font_path = None
        for candidate in font_candidates:
            if candidate and os.path.exists(candidate):
                font_path = candidate
                print(f"✅ 找到Linux字体: {font_path}")
                break
        if not font_path:
            print("⚠️ Linux未找到中文字体，将尝试安装或下载字体")
    
    # 生成词云（使用mask的实际尺寸）
    wc_kwargs = {
        'width': mask_width,
        'height': mask_height,
        'background_color': 'white',
        'max_words': 100,
        'colormap': 'viridis',
        'mask': mask,
        'contour_width': 0,
        'contour_color': 'steelblue',
        'color_func': government_colors
    }
    
    # 只在找到有效字体时添加font_path参数
    if font_path:
        wc_kwargs['font_path'] = font_path
        print(f"✅ 词云使用字体: {font_path}")
    else:
        print("️ 未找到中文字体，词云可能显示方框")
        print("💡 解决方案: 在Codespace终端执行以下命令安装字体:")
        print("   sudo apt-get update && sudo apt-get install -y fonts-wqy-zenhei")
    
    wc = WordCloud(**wc_kwargs)
    
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

# ==================== 图表函数（政府网站风格）====================
def create_line_chart(df, x_col, y_col, title, xlabel, ylabel):
    """创建折线图（政府网站风格）"""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # 获取当前使用的中文字体
    current_font = matplotlib.rcParams['font.sans-serif'][0]
    font_prop = FontProperties(fname=current_font if os.path.exists(current_font) else None)
    
    # 政府网站配色
    ax.plot(df[x_col], df[y_col], 
            marker='o', 
            linewidth=2.5, 
            markersize=8,
            color='#C41E3A',  # 中国红
            markerfacecolor='#FFFFFF',
            markeredgecolor='#C41E3A',
            markeredgewidth=2)
    
    # 去除emoji，增大字体
    clean_title = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', title)
    ax.set_title(clean_title.strip(), 
                 fontsize=16, 
                 fontweight='bold', 
                 pad=15,
                 color='#8B4513',  # 金棕色标题
                 fontproperties=font_prop)
    
    ax.set_xlabel(xlabel, fontsize=13, color='#666666', fontproperties=font_prop)
    ax.set_ylabel(ylabel, fontsize=13, color='#666666', fontproperties=font_prop)
    ax.tick_params(axis='both', which='major', labelsize=12, colors='#333333')
    
    # 政府网站风格网格
    ax.grid(True, 
            alpha=0.3, 
            color='#DAA520',  # 金色网格
            linestyle='--',
            linewidth=0.8)
    
    # 坐标轴样式
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#C41E3A')
    ax.spines['bottom'].set_color('#C41E3A')
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def create_pie_chart(data, title):
    """创建饼图（政府网站风格）"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 获取当前使用的中文字体
    current_font = matplotlib.rcParams['font.sans-serif'][0]
    font_prop = FontProperties(fname=current_font if os.path.exists(current_font) else None)
    
    # 政府网站配色
    colors = ['#228B22', '#DAA520', '#C41E3A']  # 深绿、金色、中国红
    wedges, texts, autotexts = ax.pie(
        data.values, 
        labels=data.index, 
        autopct='%1.1f%%', 
        colors=colors, 
        startangle=90,
        textprops={'fontsize': 14, 'color': '#333333', 'fontproperties': font_prop},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    
    # 增大标题字体
    clean_title = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', title)
    ax.set_title(clean_title.strip(), 
                 fontsize=16, 
                 fontweight='bold', 
                 pad=20,
                 color='#8B4513',  # 金棕色标题
                 fontproperties=font_prop)
    
    plt.tight_layout()
    return fig

# ==================== 数据加载 ====================
@st.cache_data(ttl=3600)  # 缓存1小时
def load_data():
    """加载数据（优化版：优先使用预计算数据）"""
    # 优先使用预计算的情感数据文件
    if os.path.exists('news_with_sentiment.csv'):
        print("✅ 使用预计算的情感数据文件，加载速度快")
        df = pd.read_csv('news_with_sentiment.csv')
    elif os.path.exists('news_with_keywords.csv'):
        df = pd.read_csv('news_with_keywords.csv')
        
        # 检查是否已有情感分析结果
        if 'sentiment' not in df.columns:
            print("️ 数据文件缺少sentiment列，正在计算...")
            sentiments = []
            total = len(df)
            
            # 显示进度（仅首次）
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, row in df.iterrows():
                score = calculate_sentiment_v2(row.get('content', ''), row.get('title', ''))
                sentiments.append(score)
                
                # 每500条更新一次进度
                if (idx + 1) % 500 == 0:
                    progress = (idx + 1) / total
                    progress_bar.progress(progress)
                    status_text.text(f"情感分析进度: {idx + 1}/{total} ({progress*100:.1f}%)")
            
            df['sentiment'] = sentiments
            progress_bar.progress(1.0)
            status_text.text("✅ 情感分析完成！")
            
            # 保存带情感的CSV
            df.to_csv('news_with_sentiment.csv', index=False, encoding='utf-8-sig')
            print("✅ 已保存 news_with_sentiment.csv")
        else:
            print("✅ 使用已缓存的情感分析数据")
    else:
        st.error("❌ 未找到数据文件")
        return None
    
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
        display_metric_simple(f"{neg:,}", " 负面新闻", "negative")
    with col5:
        neu = len(df[df['sentiment_category'] == 'neutral'])
        display_metric_simple(f"{neu:,}", "😐 中性新闻", "neutral")
    
    # 月度趋势
    st.markdown('<div class="subsection-title"> 月度趋势分析</div>', unsafe_allow_html=True)
    
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
        fig1 = create_line_chart(monthly, 'year_month', 'count', '月度新闻数量趋势', '月份', '数量')
        st.pyplot(fig1)
    with col2:
        fig2 = create_line_chart(monthly, 'year_month', 'avg_sent', '月度平均情感趋势', '月份', '得分')
        st.pyplot(fig2)
    
    col3, col4 = st.columns(2)
    with col3:
        fig3 = create_line_chart(monthly, 'year_month', 'pos_count', '月度正面新闻趋势', '月份', '数量')
        st.pyplot(fig3)
    with col4:
        fig4 = create_line_chart(monthly, 'year_month', 'neg_count', '月度负面新闻趋势', '月份', '数量')
        st.pyplot(fig4)
    
    # 情感分布饼图 + 总体词云（标题完全对称）
    st.markdown('<div class="subsection-title">📊 情感分布与词云</div>', unsafe_allow_html=True)
        
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="subsection-title">总体情感分布</div>', unsafe_allow_html=True)
        sentiment_dist = df['sentiment_category'].value_counts()
        labels = {'positive': '正面', 'neutral': '中性', 'negative': '负面'}
        sentiment_dist.index = [labels.get(c, c) for c in sentiment_dist.index]
        fig5 = create_pie_chart(sentiment_dist, '')
        st.pyplot(fig5)
        
    with col2:
        st.markdown('<div class="subsection-title">全部新闻词云</div>', unsafe_allow_html=True)
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
        st.dataframe(hot_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无热点关键词数据")

# ==================== 月度详情页 ====================
def show_monthly(df):
    """月度详情"""
    st.markdown('<div class="section-title"> 月度详细分析</div>', unsafe_allow_html=True)
    
    # 功能1: 月份选择器
    months = sorted(df['year_month'].unique(), reverse=True)
    month_options = [str(m) for m in months]
    selected = st.selectbox(" 选择月份", month_options, index=0)
    
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
        
    # 负面新闻预警功能
    st.markdown('<div class="subsection-title">⚠️ 负面新闻预警</div>', unsafe_allow_html=True)
    
    if neg > 0:
        # 获取情感得分最低的3条负面新闻
        negative_news = month_df[month_df['sentiment_category'] == 'negative'].copy()
        negative_news = negative_news.sort_values('sentiment').head(3)
        
        neg_ratio = neg / len(month_df) * 100
        if neg_ratio > 5 or neg > 10:
            st.warning(f"️ **本月检测到 {neg} 条负面新闻（占比 {neg_ratio:.1f}%）**，请密切关注以下高风险舆情：")
        else:
            st.info(f"ℹ️ 本月检测到 {neg} 条负面新闻，舆情整体平稳。以下为最负面新闻：")
        
        # 显示最负面的3条新闻
        for idx, row in negative_news.iterrows():
            with st.container():
                col_title, col_badge = st.columns([4, 1])
                with col_title:
                    st.markdown(f"**📰 {row['title']}**")
                with col_badge:
                    st.markdown(f"<span style='background: #d62728; color: white; padding: 0.2rem 0.6rem; border-radius: 15px; font-weight: bold; font-size: 0.8rem;'>负面 {row['sentiment']:.2f}</span>", unsafe_allow_html=True)
                
                st.caption(f"📅 {row['date'].strftime('%Y-%m-%d')}")
                
                # 添加查看正文功能
                with st.expander(" 查看正文", expanded=False):
                    st.write(row['content'])
    else:
        st.success("✅ 本月无负面新闻，舆情整体良好！")
    
    # 本月词云 + 热点关键词
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="subsection-title">本月词云</div>', unsafe_allow_html=True)
        wordcloud_img = generate_wordcloud_from_titles(month_df['title'].tolist(), mask_file='guangdong_true_mask.png')
        if wordcloud_img:
            # 与表格等高对齐
            st.image(wordcloud_img, width=480)
        else:
            st.info("暂无词云数据")
    
    with col2:
        st.markdown('<div class="subsection-title">本月热点关键词 TOP 10</div>', unsafe_allow_html=True)
        
        hot_file = 'monthly_hot_topics.csv'
        if os.path.exists(hot_file):
            hot_df = pd.read_csv(hot_file)
            month_key = selected
            month_data = hot_df[hot_df['month'] == month_key]
            
            if len(month_data) > 0:
                top10 = month_data.head(10)
                # 根据实际列名映射：rank, word, frequency
                display_df = top10[['rank', 'word', 'frequency']].copy()
                display_df.columns = ['排名', '关键词', '出现次数']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"暂无 {selected} 的热点关键词数据")
        else:
            # 动态生成
            hot_topics = extract_hot_topics_from_titles(month_df['title'].tolist(), top_n=10)
            if hot_topics:
                hot_df = pd.DataFrame(hot_topics, columns=['关键词', '出现次数'])
                hot_df.insert(0, '排名', range(1, len(hot_df) + 1))
                st.dataframe(hot_df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无热点关键词数据")
    
    # 本月新闻列表
    st.markdown('<div class="subsection-title"> 本月新闻列表</div>', unsafe_allow_html=True)
    
    # 功能2: 关键词搜索
    search_col, _ = st.columns([1, 4])
    with search_col:
        search_keyword = st.text_input(" 搜索关键词", placeholder="输入关键词...")
    
    if search_keyword:
        filtered_df = month_df[
            month_df['title'].str.contains(search_keyword, case=False, na=False) |
            month_df['content'].str.contains(search_keyword, case=False, na=False)
        ]
    else:
        filtered_df = month_df
    
    if len(filtered_df) == 0:
        st.info("未找到匹配的新闻")
    else:
        # 分页显示，每页20条新闻
        page_size = 20
        total_pages = (len(filtered_df) + page_size - 1) // page_size
        
        # 添加分页器（左右滑动的滑动轴）
        if total_pages > 1:
            page_col1, page_col2, page_col3 = st.columns([1, 3, 1])
            with page_col2:
                current_page = st.slider(
                    "页面切换",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1,
                    label_visibility="collapsed"
                )
                st.caption(f"第 {current_page} / {total_pages} 页（每页 {page_size} 条）")
        else:
            current_page = 1
        
        # 计算当前页的新闻索引
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(filtered_df))
        current_page_news = filtered_df.iloc[start_idx:end_idx]
        
        st.info(f"💡 共 {len(filtered_df)} 条新闻，当前显示第 {start_idx + 1}-{end_idx} 条。点击「查看正文」展开内容。")
        
        # 使用垂直列表显示当前页的新闻，每条新闻占一行
        for idx, row in current_page_news.iterrows():
            cat, label, color = get_sentiment_info(row['sentiment'])
            
            with st.container():
                # 使用columns布局：标题和情感标签在同一行
                col_title, col_badge, col_date = st.columns([6, 1, 2])
                
                with col_title:
                    st.markdown(f"**{row['title']}**")
                
                with col_badge:
                    st.markdown(
                        f"<span style='background:{color}; color:white; padding: 0.3rem 0.8rem; border-radius: 15px; font-weight: bold; font-size: 0.85rem; display: inline-block; text-align: center;'>{label}</span>",
                        unsafe_allow_html=True
                    )
                
                with col_date:
                    st.markdown(f"<span style='color: #7f8c8d; font-size: 0.85rem;'> {row['date'].strftime('%Y-%m-%d')}</span>", unsafe_allow_html=True)
                
                # 使用expander显示正文
                with st.expander("📄 查看正文", expanded=False):
                    st.write(row['content'])
                
                # 添加分隔线
                st.markdown("---")
        
        # 底部再次添加分页器，方便翻页
        if total_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            page_col1, page_col2, page_col3 = st.columns([1, 3, 1])
            with page_col2:
                bottom_page = st.slider(
                    "翻页控制",
                    min_value=1,
                    max_value=total_pages,
                    value=current_page,
                    step=1,
                    label_visibility="collapsed",
                    key="bottom_slider"
                )

# ==================== 主程序 ====================
def main():
    """主程序"""
    st.markdown('<div class="main-title">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)
    
    # 加载数据
    df = load_data()
    
    if df is None or len(df) == 0:
        st.error("❌ 数据加载失败")
        return
    
    # 侧边栏导航
    st.sidebar.markdown("### 📌 导航菜单")
    page = st.sidebar.radio(
        "选择页面",
        ["🏠 全局概览", "📅 月度详情"]
    )
    
    # 显示当前页面（调试用）
    st.sidebar.info(f"当前页面: {page}")
    
    # 页面路由
    if page == "🏠 全局概览":
        show_overview(df)
    else:
        show_monthly(df)

if __name__ == "__main__":
    main()
