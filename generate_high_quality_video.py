#!/usr/bin/env python3
"""
生成高质量1分钟视频
优化内容结构和视觉效果
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config.settings import cfg
from openai import OpenAI

client = OpenAI(api_key=cfg.llm_api_key, base_url=cfg.llm_api_base)

def generate_high_quality_content():
    """生成高质量视频内容"""
    
    system_prompt = """你是顶级短视频内容策划专家，专门制作1分钟高质量知识类短视频。
    
视频要求：
1. 时长：55-65秒
2. 结构：开场钩子 + 3-5个核心观点 + 结尾行动号召
3. 内容：深度、有价值、有洞察力
4. 风格：专业但不枯燥，有感染力

输出严格的JSON格式，不要markdown代码块。"""

    topics = [
        "AI如何改变未来工作",
        "Web3和去中心化互联网",
        "个人品牌建设的核心策略", 
        "高效学习的科学方法",
        "创业者的思维模式",
        "数字游民的生活方式",
        "心理健康与工作效率",
        "投资理财的基础认知"
    ]
    
    import random
    topic = random.choice(topics)
    
    user_prompt = f"""请为话题"{topic}"创作一个1分钟高质量短视频脚本。

要求：
1. 视频总时长：60秒左右
2. 开场钩子：10秒内抓住注意力
3. 核心内容：3-5个关键点，每个点8-12秒
4. 结尾：行动号召和总结

输出JSON格式：
{{
  "type": "A",
  "title": "视频标题（12字内）",
  "hook": "开场钩子文案（15字内）",
  "slides": [
    {{"text": "第1个核心观点", "duration": 10.0, "style": "emphasis"}},
    {{"text": "详细解释或案例", "duration": 8.0, "style": "normal"}},
    {{"text": "第2个核心观点", "duration": 10.0, "style": "emphasis"}},
    {{"text": "详细解释或案例", "duration": 8.0, "style": "normal"}},
    {{"text": "第3个核心观点", "duration": 10.0, "style": "emphasis"}},
    {{"text": "详细解释或案例", "duration": 8.0, "style": "normal"}}
  ],
  "cta": "结尾行动号召（12字内）",
  "color_scheme": "gradient",
  "font_style": "bold",
  "total_duration": 60.0
}}"""

    print(f"生成高质量视频内容，话题: {topic}")
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=cfg.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                max_tokens=1500,
            )
            
            content = response.choices[0].message.content.strip()
            
            # 清理响应内容
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            task = json.loads(content)
            
            # 验证时长
            total_duration = 1.5  # 开场
            for slide in task.get('slides', []):
                total_duration += slide.get('duration', 2.5)
            total_duration += 2.0  # 结尾
            
            task['total_duration'] = round(total_duration, 1)
            task['quality_level'] = "high"
            task['topic'] = topic
            task['created_at'] = datetime.now().isoformat()
            task['status'] = "pending"
            
            print(f"生成成功！预计时长: {task['total_duration']}秒")
            print(f"标题: {task['title']}")
            print(f"幻灯片数: {len(task['slides'])}")
            
            return task
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败，尝试 {attempt + 1}/3: {e}")
            if attempt == 2:
                raise
        except Exception as e:
            print(f"生成失败: {e}")
            raise
    
    return None

def save_and_render(task_data):
    """保存并渲染视频"""
    
    # 保存任务文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_file = cfg.tasks_dir / f"hq_{timestamp}_task.json"
    task_file.parent.mkdir(exist_ok=True)
    
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=2, ensure_ascii=False)
    
    print(f"任务文件已保存: {task_file}")
    
    # 输出视频文件
    output_file = cfg.output_dir / f"hq_{timestamp}_video.mp4"
    output_file.parent.mkdir(exist_ok=True)
    
    # 调用Remotion渲染（高质量模式）
    remotion_dir = Path("skills/remotion")
    render_script = remotion_dir / "render_enhanced.sh"
    
    if render_script.exists():
        import subprocess
        
        print(f"开始渲染高质量视频...")
        print(f"输出文件: {output_file}")
        
        # 使用high_quality配置渲染
        cmd = [
            "bash", str(render_script),
            str(task_file.relative_to(remotion_dir.parent.parent)),
            str(output_file.relative_to(remotion_dir.parent.parent)),
            "high_quality"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=remotion_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            print("✅ 高质量视频渲染成功！")
            print(result.stdout)
            
            # 检查文件大小
            if output_file.exists():
                file_size = output_file.stat().st_size
                file_size_mb = file_size / (1024 * 1024)
                print(f"视频文件大小: {file_size_mb:.2f} MB")
                
                # 获取视频时长（通过文件大小估算）
                # 通常1分钟1080p视频约10-20MB
                if 5 < file_size_mb < 50:
                    print(f"✅ 视频文件大小正常 ({file_size_mb:.1f} MB)")
                else:
                    print(f"⚠️ 视频文件大小异常 ({file_size_mb:.1f} MB)")
                
                return str(output_file)
            else:
                print("❌ 输出文件未生成")
                return None
        else:
            print("❌ 渲染失败")
            print("错误输出:", result.stderr)
            return None
    else:
        print(f"❌ 渲染脚本不存在: {render_script}")
        return None

def main():
    print("=== 生成高质量1分钟视频 ===\n")
    
    try:
        # 1. 生成高质量内容
        task_data = generate_high_quality_content()
        
        if not task_data:
            print("内容生成失败")
            return
        
        # 2. 保存并渲染
        print("\n开始渲染视频...")
        video_file = save_and_render(task_data)
        
        if video_file:
            print(f"\n🎉 高质量视频生成完成！")
            print(f"视频文件: {video_file}")
            print(f"预计时长: {task_data['total_duration']}秒")
            print(f"话题: {task_data['topic']}")
            print(f"质量等级: {task_data['quality_level']}")
            
            # 添加到渲染队列
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from skills.queue.queue_manager import enqueue, mark_done
                
                enqueue(str(Path(task_data['task_file']) if 'task_file' in task_data else ""))
                mark_done(str(Path(task_data['task_file']) if 'task_file' in task_data else ""), True)
                print("✅ 任务已加入队列并标记完成")
            except:
                print("⚠️ 队列操作跳过")
        else:
            print("\n❌ 视频生成失败")
            
    except Exception as e:
        print(f"\n❌ 生成过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()