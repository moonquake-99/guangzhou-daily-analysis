import streamlit as st
import pandas as pd

st.set_page_config(page_title="测试", layout="wide")

# 读取数据
df = pd.read_csv('news_with_keywords.csv')

st.title("测试页面 - 5个平级指标")

# 创建5个平级卡片
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📰 新闻总数", f"{len(df):,}")

with col2:
    st.metric("💭 平均情感", "0.750")

with col3:
    st.metric("✅ 正面新闻", "5000")

with col4:
    st.metric("❌ 负面新闻", "500")

with col5:
    st.metric("😐 中性新闻", "1202")

st.success("如果能看到这5个卡片，说明布局正确！")
