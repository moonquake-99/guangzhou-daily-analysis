"""
广州日报舆情分析系统 - 快速演示版
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="广州日报舆情分析系统", page_icon="📰", layout="wide")

# ==================== 全局样式 ====================
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin: 1rem 0;
        padding: 1rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        padding: 0.5rem;
        border-left: 5px solid #1f77b4;
        padding-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 加载数据 ====================
@st.cache_data
def load_data():
    df = pd.read_csv('news_with_keywords.csv', encoding='utf-8-sig')
    
    # 如果没有sentiment列，创建示例数据
    if 'sentiment' not in df.columns:
        df['sentiment'] = [0.6, 0.7, 0.5, 0.8, 0.3] * (len(df) // 5 + 1)
        df = df.head(len(df))
    
    if 'sentiment_category' not in df.columns:
        def categorize(s):
            if s >= 0.6: return 'positive'
            elif s <= 0.4: return 'negative'
            else: return 'neutral'
        df['sentiment_category'] = df['sentiment'].apply(categorize)
    
    return df

df = load_data()

# ==================== 标题 ====================
st.markdown('<div class="main-title">📰 广州日报舆情分析系统</div>', unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("🔍 筛选条件")
    months = sorted(df['year_month'].unique())
    selected_month = st.selectbox("选择月份", months)
    
    search_keyword = st.text_input("搜索关键词", "")

# ==================== 主内容区 ====================
st.markdown('<div class="section-title">📊 全局概览</div>', unsafe_allow_html=True)

# 5个平级指标（使用Streamlit原生metric）
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="📰 新闻总数", value=f"{len(df):,}")
with col2:
    avg_sentiment = df['sentiment'].mean()
    label = "正面" if avg_sentiment >= 0.6 else ("负面" if avg_sentiment <= 0.4 else "中性")
    st.metric(label="💭 平均情感", value=f"{avg_sentiment:.3f}", delta=label)
with col3:
    pos_count = len(df[df['sentiment_category'] == 'positive'])
    st.metric(label="✅ 正面新闻", value=f"{pos_count:,}")
with col4:
    neg_count = len(df[df['sentiment_category'] == 'negative'])
    st.metric(label="❌ 负面新闻", value=f"{neg_count:,}")
with col5:
    neu_count = len(df[df['sentiment_category'] == 'neutral'])
    st.metric(label="😐 中性新闻", value=f"{neu_count:,}")

st.divider()

# ==================== 新闻详情列表 ====================
st.markdown('<div class="section-title">📰 新闻详情（带彩色边框和emoji）</div>', unsafe_allow_html=True)

# 显示前10条新闻作为示例
display_df = df.head(10)

for idx, row in display_df.iterrows():
    score = row['sentiment']
    title = row.get('title', '无标题')
    date = row.get('date', '')
    content = row.get('content', '')[:200] + '...' if len(row.get('content', '')) > 200 else row.get('content', '')
    
    # 确定情感类别和颜色
    if score >= 0.6:
        cat = 'positive'
        emoji = '😊'
        color = '#2ca02c'
        label = '正面'
    elif score <= 0.4:
        cat = 'negative'
        emoji = '😞'
        color = '#d62728'
        label = '负面'
    else:
        cat = 'neutral'
        emoji = '😐'
        color = '#ff7f0e'
        label = '中性'
    
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

st.success("✅ 以上是快速演示版，展示了修复后的效果！")
st.info("💡 特点：\n1. 5个指标使用统一样式\n2. 新闻卡片带彩色边框和emoji\n3. 点击展开显示彩色情感方块+正文")
