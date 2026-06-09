"""
自动更新脚本 - 整合爬虫、清洗、情感分析、上传全流程
每天凌晨2点自动执行
"""

import os
import sys
from datetime import datetime
import subprocess

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"命令: {cmd}\n")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✅ 执行成功")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ 执行失败")
            print(f"错误信息: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("🚀 广州日报舆情系统 - 自动更新流程启动")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    steps = [
        {
            'cmd': 'python crawl_gzdaily.py',
            'desc': '步骤1: 爬取最新新闻'
        },
        {
            'cmd': 'python data_cleaning.py',
            'desc': '步骤2: 数据清洗和关键词提取'
        },
        {
            'cmd': 'python extract_hot_topics or word cloud.py',
            'desc': '步骤3: 提取热点关键词'
        }
    ]
    
    # 执行所有步骤
    success_count = 0
    for step in steps:
        if run_command(step['cmd'], step['desc']):
            success_count += 1
        else:
            print(f"\n⚠️ {step['desc']} 失败，但继续执行后续步骤")
    
    print(f"\n{'='*60}")
    print(f"📊 更新完成统计")
    print(f"{'='*60}")
    print(f"总步骤数: {len(steps)}")
    print(f"成功步骤: {success_count}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(steps):
        print("\n✅ 所有步骤执行成功！")
        print("💡 下一步: 请手动将 news_with_keywords.csv 上传到GitHub")
    else:
        print(f"\n⚠️ 有 {len(steps) - success_count} 个步骤失败，请检查日志")
    
    return success_count == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
