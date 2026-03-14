"""
LLM 内容分析器：读取 raw JSON → 调用 LLM → 输出 Type A / Type B 任务 JSON
用法: python llm_analyst.py <raw_json_path>
"""
import json
import sys
import time
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import cfg

client = OpenAI(api_key=cfg.llm_api_key, base_url=cfg.llm_api_base)

SYSTEM_PROMPT = """你是一个抖音内容策划专家。分析 X (Twitter) 爆款推文，判断最适合的视频形式并输出结构化任务。

视频类型规则：
- Type A（文字动画）：适合观点类、金句类、列表类内容。纯文字排版动画，无需素材。
- Type B（混剪）：适合故事类、事件类、有画面感的内容。需要配音+字幕+背景视频。

输出严格 JSON，不要 markdown 代码块，不要任何解释文字。"""

USER_PROMPT_TEMPLATE = """分析以下推文，选出最适合做成抖音视频的1条，输出任务 JSON。

推文列表：
{tweets}

输出格式二选一：

Type A:
{{
  "type": "A",
  "source_tweet_id": "...",
  "title": "视频标题（15字内）",
  "hook": "开场钩子文案（10字内）",
  "slides": [
    {{"text": "第1屏文字", "duration": 2.5}},
    {{"text": "第2屏文字", "duration": 2.5}}
  ],
  "cta": "结尾行动号召（10字内）",
  "color_scheme": "dark",
  "font_style": "bold"
}}

Type B:
{{
  "type": "B",
  "source_tweet_id": "...",
  "title": "视频标题（15字内）",
  "narration_script": "完整旁白文案（200字内，口语化）",
  "subtitles": [
    {{"start": 0.0, "end": 3.0, "text": "字幕段落1"}},
    {{"start": 3.0, "end": 6.0, "text": "字幕段落2"}}
  ],
  "bgm_style": "upbeat",
  "bg_video_keyword": "background video keyword in English"
}}"""


def analyze(raw_path: Path) -> Path:
    raw = json.loads(raw_path.read_text())
    top5 = raw[:5]
    tweets_text = "\n\n".join(
        f"[{i+1}] @{t['author']} ({t['likes']} likes)\n{t['text']}"
        for i, t in enumerate(top5)
    )

    task = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=cfg.llm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(tweets=tweets_text)},
                ],
                temperature=0.7,
                max_tokens=1500,
            )
            content = resp.choices[0].message.content.strip()
            
            # 清理响应内容（移除markdown代码块）
            if content.startswith('```json'):
                content = content[7:]  # 移除 ```json
            if content.startswith('```'):
                content = content[3:]  # 移除 ```
            if content.endswith('```'):
                content = content[:-3]  # 移除结尾的 ```
            content = content.strip()
            
            task = json.loads(content)
            break
        except json.JSONDecodeError:
            if attempt == 2:
                raise
            time.sleep(2)

    task["created_at"] = raw[0]["scraped_at"] if raw else ""
    task["status"] = "pending"

    out = raw_path.parent / raw_path.name.replace("_raw.json", "_task.json")
    out.write_text(json.dumps(task, ensure_ascii=False, indent=2))
    print(f"[analyst] Type {task['type']} 任务 → {out}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python llm_analyst.py <raw_json_path>")
        sys.exit(1)
    analyze(Path(sys.argv[1]))
