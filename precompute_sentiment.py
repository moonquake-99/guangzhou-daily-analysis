"""
预先计算情感分析并保存，提升应用启动速度
"""
import pandas as pd
import jieba
from snownlp import SnowNLP
import time

# 自定义词典
CUSTOM_WORDS = [
    '全运会', '十五运会', '十五届全运会', '残运会', '特奥会',
    '大湾区', '粤港澳大湾区', '前海', '横琴', '南沙',
    '高质量发展', '数字经济', '人工智能', 'AI', '大模型',
    '乡村振兴', '共同富裕', '碳中和', '碳达峰', '双碳',
]

for word in CUSTOM_WORDS:
    jieba.add_word(word)

# 情感关键词
NEGATIVE_KEYWORDS = {
    '危机', '灾难', '事故', '问题', '困难', '挑战',
    '下降', '减少', '降低', '恶化', '衰退', '萧条',
    '冲突', '矛盾', '争议', '纠纷', '诉讼', '违法',
    '批评', '指责', '谴责', '不满', '反对', '抵制',
    '失败', '损失', '亏损', '倒闭', '破产', '裁员',
    '污染', '破坏', '违规', '造假', '欺诈',
}

POSITIVE_KEYWORDS = {
    '成功', '成就', '突破', '创新', '发展', '进步', '提升',
    '优秀', '良好', '优异', '卓越', '突出', '显著',
    '增长', '增加', '上升', '改善', '优化', '完善',
    '合作', '共赢', '友好', '和谐', '稳定', '安全', '保障',
    '支持', '帮助', '援助', '促进', '推动', '助力',
    '庆祝', '祝贺', '表彰', '奖励', '荣誉', '赞扬', '肯定',
}

def calculate_sentiment(content, title=''):
    """计算情感分数"""
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
    
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    
    if negative_count > positive_count:
        base_score = base_score * 0.7
    elif positive_count > negative_count:
        base_score = base_score * 0.3 + 0.7
    
    return max(0.0, min(1.0, base_score))

# 加载数据
print(" 加载数据文件...")
df = pd.read_csv('news_with_keywords.csv')
print(f"✅ 加载完成，共 {len(df)} 条新闻")

# 计算情感分析
print("\n🔍 开始情感分析（这可能需要几分钟）...")
start_time = time.time()

sentiments = []
total = len(df)

for idx, row in df.iterrows():
    score = calculate_sentiment(row.get('content', ''), row.get('title', ''))
    sentiments.append(score)
    
    # 每500条显示进度
    if (idx + 1) % 500 == 0:
        elapsed = time.time() - start_time
        speed = (idx + 1) / elapsed
        remaining = (total - idx - 1) / speed
        print(f"  进度: {idx + 1}/{total} ({(idx+1)/total*100:.1f}%) - 预计剩余 {remaining:.0f}秒")

df['sentiment'] = sentiments

elapsed_time = time.time() - start_time
print(f"\n✅ 情感分析完成！用时 {elapsed_time:.1f} 秒")

# 保存结果
print("\n💾 保存带情感分析的数据...")
df.to_csv('news_with_sentiment.csv', index=False, encoding='utf-8-sig')
print("✅ 已保存到 news_with_sentiment.csv")

# 统计信息
print("\n📊 情感分布统计：")
df['category'] = df['sentiment'].apply(lambda x: '正面' if x > 0.6 else ('负面' if x < 0.4 else '中性'))
print(df['category'].value_counts())

print("\n🎉 完成！现在可以运行 app_final_v3.py，速度会快很多！")
