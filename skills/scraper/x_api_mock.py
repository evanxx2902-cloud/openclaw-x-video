#!/usr/bin/env python3
"""
X API 模拟器 - 用于测试完整流程
在获取真实X API Key之前，使用模拟数据
"""
import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import cfg

def generate_mock_tweets(limit=20, min_likes=500):
    """生成模拟推文数据"""
    
    # 热门话题和内容
    topics = [
        "AI人工智能",
        "创业投资", 
        "科技趋势",
        "加密货币",
        "职场发展",
        "个人成长",
        "健康生活",
        "效率工具"
    ]
    
    authors = [
        "TechGuru42",
        "StartupFounder",
        "AIAnalyst",
        "CryptoExpert",
        "CareerCoach",
        "ProductivityPro",
        "HealthEnthusiast",
        "BusinessLeader"
    ]
    
    templates = [
        "研究发现：{topic}领域正在发生重大变革。{insight}",
        "创业者必读：关于{topic}的3个关键洞察。{insight}",
        "2024年{topic}趋势预测：{insight}",
        "为什么{topic}如此重要？{insight}",
        "专家分享：{topic}的最佳实践。{insight}"
    ]
    
    insights = [
        "这将彻底改变行业格局",
        "99%的人都忽略了这一点",
        "数据表明增长潜力巨大",
        "早期采用者已获得显著优势",
        "这是未来5年的关键技能"
    ]
    
    results = []
    for i in range(limit):
        topic = random.choice(topics)
        author = random.choice(authors)
        template = random.choice(templates)
        insight = random.choice(insights)
        
        # 生成推文内容
        text = template.format(topic=topic, insight=insight)
        
        # 生成互动数据（确保超过min_likes）
        likes = random.randint(min_likes, min_likes * 10)
        retweets = random.randint(likes // 10, likes // 5)
        replies = random.randint(likes // 20, likes // 10)
        
        # 生成时间（最近7天内）
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        scraped_at = (datetime.now() - timedelta(days=days_ago, hours=hours_ago)).isoformat()
        
        tweet_data = {
            "author": author,
            "text": text,
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "tweet_id": f"mock_{i}_{int(datetime.now().timestamp())}",
            "scraped_at": scraped_at
        }
        
        results.append(tweet_data)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="X API 模拟器")
    parser.add_argument("--limit", type=int, default=20, help="抓取数量")
    parser.add_argument("--min-likes", type=int, default=500, help="最小点赞数")
    parser.add_argument("--output", type=str, help="输出文件路径")
    
    args = parser.parse_args()
    
    print("[x_api_mock] 生成模拟推文数据...")
    tweets = generate_mock_tweets(args.limit, args.min_likes)
    
    # 输出文件路径
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = cfg.tasks_dir / f"{timestamp}_raw.json"
    
    # 确保目录存在
    output_path.parent.mkdir(exist_ok=True)
    
    # 保存数据
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False)
    
    print(f"[x_api_mock] 已生成 {len(tweets)} 条模拟推文")
    print(f"[x_api_mock] 数据保存至: {output_path}")
    
    # 打印摘要
    print("\n数据摘要:")
    print(f"总推文数: {len(tweets)}")
    print(f"平均点赞数: {sum(t['likes'] for t in tweets) // len(tweets)}")
    print(f"最高点赞数: {max(t['likes'] for t in tweets)}")
    print(f"示例推文: {tweets[0]['text'][:80]}...")
    
    return str(output_path)

if __name__ == "__main__":
    try:
        output_file = main()
        print(f"\n下一步: python skills/analyst/llm_analyst.py {output_file}")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)