#!/usr/bin/env python3
"""
智能X抓取器 - 优先使用真实API，失败时使用模拟数据
"""
import json
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import cfg

def try_real_api(limit, min_likes):
    """尝试使用真实X API"""
    print("[scraper] 尝试使用真实X API...")
    
    # 检查是否有API Key
    api_key = getattr(cfg, 'x_api_key', None)
    if not api_key:
        print("[scraper] 未配置X API Key，跳过真实API")
        return None
    
    try:
        # 这里可以集成真实的X API调用
        # 暂时返回None表示需要模拟数据
        print("[scraper] X API Key已配置，但需要实现具体API调用")
        print("[scraper] 提示：申请X API Key: https://developer.twitter.com")
        return None
        
    except Exception as e:
        print(f"[scraper] 真实API调用失败: {e}")
        return None

def use_mock_data(limit, min_likes):
    """使用模拟数据"""
    print("[scraper] 使用模拟数据...")
    
    try:
        # 导入模拟数据生成器
        from x_api_mock import generate_mock_tweets
        tweets = generate_mock_tweets(limit, min_likes)
        
        # 保存数据
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = cfg.tasks_dir / f"{timestamp}_raw.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tweets, f, indent=2, ensure_ascii=False)
        
        print(f"[scraper] 已生成 {len(tweets)} 条模拟推文")
        print(f"[scraper] 数据保存至: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"[scraper] 模拟数据生成失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="智能X抓取器")
    parser.add_argument("--limit", type=int, default=20, help="抓取数量")
    parser.add_argument("--min-likes", type=int, default=500, help="最小点赞数")
    parser.add_argument("--force-mock", action="store_true", help="强制使用模拟数据")
    
    args = parser.parse_args()
    
    print(f"[scraper] 开始抓取，限制: {args.limit}条，最小点赞: {args.min_likes}")
    
    output_file = None
    
    if not args.force_mock:
        # 先尝试真实API
        output_file = try_real_api(args.limit, args.min_likes)
    
    # 如果真实API失败或强制使用模拟数据
    if not output_file:
        output_file = use_mock_data(args.limit, args.min_likes)
    
    if output_file:
        print(f"\n[scraper] 抓取完成！输出文件: {output_file}")
        print(f"[scraper] 下一步: python skills/analyst/llm_analyst.py {output_file}")
        return output_file
    else:
        print("[scraper] 抓取失败")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[scraper] 错误: {e}")
        sys.exit(1)