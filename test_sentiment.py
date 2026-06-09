"""测试情感分析效果"""
from snownlp import SnowNLP
import pandas as pd

print("="*70)
print("广州日报舆情分析系统 - 情感分析测试")
print("="*70)

df = pd.read_csv('news_with_keywords.csv', nrows=5)

print('\n测试前5条新闻的情感分析:\n')
print('='*70)

for idx, row in df.iterrows():
    sentiment_score = SnowNLP(row['content']).sentiments
    
    if sentiment_score > 0.6:
        category = '✅ 正面'
        emoji = '😊'
    elif sentiment_score < 0.4:
        category = '❌ 负面'
        emoji = '😟'
    else:
        category = '➖ 中性'
        emoji = '😐'
    
    print(f'\n第{idx+1}条:')
    print(f'  标题: {row["title"][:50]}...')
    print(f'  情感得分: {sentiment_score:.4f}')
    print(f'  情感类别: {emoji} {category}')
    print('-'*70)

print('\n' + '='*70)
print('测试完成！现在可以运行: streamlit run app.py')
print('='*70)
