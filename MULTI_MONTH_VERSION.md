# 广州日报新闻爬虫 - 多月份多版面版本

## 更新说明
已更新爬虫以支持爬取多个月份和多个版面的数据。

## 目标月份
本次爬取以下6个月的数据：
- 2025年11月
- 2025年12月
- 2026年1月
- 2026年2月
- 2026年3月
- 2026年4月（重新爬取以保持数据结构一致）

## 目标版面（共12个版面）
- A1版：头版
- A2版：跑出加速度 干出新业绩
- A3版：科技广州新观察
- A4版：评论
- A5版：要闻
- A6版：粤韵
- A7版：A7版
- A8版：要闻
- A9版：要闻
- A10版：综合
- A11版：健康周刊
- A12版：科技周刊

## 数据存储结构
```
news_data/
├── 2025-11/                 # 2025年11月数据
│   ├── A1/                  # A1版（头版）
│   │   ├── 2025-11-01.json
│   │   ├── 2025-11-02.json
│   │   └── ...
│   ├── A2/                  # A2版（跑出加速度 干出新业绩）
│   │   ├── 2025-11-01.json
│   │   └── ...
│   ├── A3/                  # A3版（科技广州新观察）
│   ├── A4/                  # A4版（评论）
│   ├── A5/                  # A5版（要闻）
│   ├── A6/                  # A6版（粤韵）
│   ├── A7/                  # A7版
│   ├── A8/                  # A8版（要闻）
│   ├── A9/                  # A9版（要闻）
│   ├── A10/                 # A10版（综合）
│   ├── A11/                 # A11版（健康周刊）
│   └── A12/                 # A12版（科技周刊）
├── 2025-12/                 # 2025年12月数据（同样结构）
├── 2026-01/                 # 2026年1月数据（同样结构）
├── 2026-02/                 # 2026年2月数据（同样结构）
├── 2026-03/                 # 2026年3月数据（同样结构）
└── 2026-04/                 # 2026年4月数据（重新爬取）
    ├── A1/
    ├── A2/
    └── ...
```

## 数据字段
每个JSON文件包含：
```json
{
  "date": "2025-11-01",
  "section": "A1",
  "section_name": "头版",
  "list_url": "https://gzdaily.dayoo.com/pc/html/2025-11/01/node_1.htm?v=1",
  "total_articles": 7,
  "success_count": 6,
  "articles": [
    {
      "title": "新闻标题",
      "content": "完整的新闻正文内容...",
      "url": "https://gzdaily.dayoo.com/pc/html/2025-11/01/content_866_898813.htm",
      "publish_date": "2025-11-01",
      "section": "A1",
      "section_name": "头版"
    }
  ]
}
```

## 使用方法

### 运行爬虫
```powershell
cd c:\Users\Administrator.DESKTOP-AODUTOR\Desktop\py
C:\PROGRAMDATA\anaconda3\python.exe gzdaily_spider.py
```

### 查看进度
```powershell
# 查看日志最后50行
Get-Content spider.log -Tail 50

# 查看某个月份某个版面的文件数量
Get-ChildItem "news_data\2025-11\A1" | Measure-Object | Select-Object -ExpandProperty Count
Get-ChildItem "news_data\2025-11\A2" | Measure-Object | Select-Object -ExpandProperty Count

# 统计所有版面的文件总数
$total = 0; Get-ChildItem "news_data\2025-11" -Directory | ForEach-Object { $total += (Get-ChildItem $_.FullName | Measure-Object).Count }; Write-Output $total
```

## 预计时间
- 每个月约30天
- 每天12个版面
- 每个版面约7-15篇文章
- 每篇文章需要约2-3秒（请求+解析）
- 每次请求间隔2秒（保守策略）
- **预计总时间：9-13小时**

**计算方式：**
```
总请求数 = 6个月 × 30天 × 12版面 × 10文章 ≈ 21,600次请求
总时间 = 21,600 × 2秒 ≈ 12小时
```

## 断点续传
- 爬虫会自动跳过已爬取的日期
- 如果中断，可以重新运行脚本继续
- 已爬取的数据不会被重复爬取

## 配置修改
如需修改爬取的月份，编辑 `gzdaily_spider.py` 中的 `MONTHS_TO_CRAWL` 列表：

```python
MONTHS_TO_CRAWL = [
    (2025, 11),
    (2025, 12),
    (2026, 1),
    (2026, 2),
    (2026, 3),
    (2026, 4),
]
```

如需修改爬取的版面，编辑 `SECTIONS_CONFIG` 字典：

```python
SECTIONS_CONFIG = {
    'A1': {'node_id': 'node_1', 'name': '头版'},
    'A2': {'node_id': 'node_867', 'name': '跑出加速度 干出新业绩'},
    # ... 其他版面
}
```

## 数据处理示例

### 读取所有月份所有版面的数据
```python
import json
import os
import glob

base_dir = 'news_data'
all_articles = []

# 遍历所有月份目录
for month_dir in sorted(glob.glob(os.path.join(base_dir, '*'))):
    if os.path.isdir(month_dir):
        # 遍历该月份下的所有版面目录
        for section_dir in sorted(glob.glob(os.path.join(month_dir, '*'))):
            if os.path.isdir(section_dir):
                for file in glob.glob(os.path.join(section_dir, '*.json')):
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_articles.extend(data['articles'])

print(f"总共爬取 {len(all_articles)} 篇文章")
```

### 按月份和版面统计
```python
import json
import os
import glob

base_dir = 'news_data'

for month_dir in sorted(glob.glob(os.path.join(base_dir, '*'))):
    if os.path.isdir(month_dir):
        month_name = os.path.basename(month_dir)
        print(f"\n{month_name}:")
        
        # 遍历该月份下的所有版面
        for section_dir in sorted(glob.glob(os.path.join(month_dir, '*'))):
            if os.path.isdir(section_dir):
                section_name = os.path.basename(section_dir)
                files = glob.glob(os.path.join(section_dir, '*.json'))
                
                total_articles = 0
                for file in files:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        total_articles += data['total_articles']
                
                print(f"  {section_name}: {len(files)} 天, {total_articles} 篇文章")
```

## 当前状态
- ⏳ 2025年11月：等待爬取（11个版面）
- ⏳ 2025年12月：等待爬取（11个版面）
- ⏳ 2026年1月：等待爬取（11个版面）
- ⏳ 2026年2月：等待爬取（11个版面）
- ⏳ 2026年3月：等待爬取（11个版面）
- ⏳ 2026年4月：等待重新爬取（11个版面）

**注意**：原有的4月A1版数据将被重新爬取并存储到新的目录结构中。

## 注意事项
1. 爬虫会自动创建月份和版面目录
2. 2026年4月数据将重新爬取以保持数据结构一致
3. 每次请求间隔2秒，避免对服务器造成压力
4. 请确保有足够的磁盘空间（预计需要200-300MB）
5. 预计总爬取时间：8-12小时
6. 支持断点续传，中断后可重新运行继续
7. 日志文件 `spider.log` 会记录详细的爬取过程
8. 如果某个版面失败，不会影响其他版面的爬取
