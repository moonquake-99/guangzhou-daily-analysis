"""
广州日报舆情分析系统 - 快速测试版（使用已保存数据）
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="广州日报舆情分析系统", page_icon="📰", layout="wide", initial_sidebar_state="expanded")

# 全局样式
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
    
    .subsection-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #34495e;
        margin: 1rem 0 0.8rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📰 广州日报舆情分析系统 - 快速测试版</div>', unsafe_allow_html=True)

# 加载数据
if os.path.exists('news_with_keywords.csv'):
    df = pd.read_csv('news_with_keywords.csv')
    
    st.markdown('<div class="section-title">📈 测试：5个平级指标（统一样式）</div>', unsafe_allow_html=True)
    
    # 5个平级指标
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="📰 新闻总数", value=f"{len(df):,}")
    with col2:
        st.metric(label="💭 平均情感", value="0.720")
    with col3:
        st.metric(label="✅ 正面新闻", value="5,200")
    with col4:
        st.metric(label="❌ 负面新闻", value="300")
    with col5:
        st.metric(label="😐 中性新闻", value="1,202")
    
    st.success("✅ 5个指标样式统一！")
    
    # 测试新闻卡片
    st.markdown('<div class="section-title">📰 测试：新闻卡片（彩色边框+emoji）</div>', unsafe_allow_html=True)
    
    # 正面新闻
    st.markdown("""
    <div style="border-left: 6px solid #2ca02c; background: linear-gradient(90deg, #2ca02c10 0%, white 100%); padding: 1rem; margin: 0.5rem 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #2c3e50; flex: 1;">庆"五一"劳模工匠座谈会召开</span>
            <span style="background:#2ca02c; color:white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; margin-left: 1rem; white-space: nowrap;">😊 正面</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 负面新闻
    st.markdown("""
    <div style="border-left: 6px solid #d62728; background: linear-gradient(90deg, #d6272810 0%, white 100%); padding: 1rem; margin: 0.5rem 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #2c3e50; flex: 1;">某地发生火灾事故造成伤亡</span>
            <span style="background:#d62728; color:white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; margin-left: 1rem; white-space: nowrap;">😟 负面</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 中性新闻
    st.markdown("""
    <div style="border-left: 6px solid #ff7f0e; background: linear-gradient(90deg, #ff7f0e10 0%, white 100%); padding: 1rem; margin: 0.5rem 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #2c3e50; flex: 1;">今日天气晴好适宜出行</span>
            <span style="background:#ff7f0e; color:white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; margin-left: 1rem; white-space: nowrap;">😐 中性</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.success("✅ 新闻卡片带彩色边框和emoji！")
    
else:
    st.error("❌ 未找到数据文件")
