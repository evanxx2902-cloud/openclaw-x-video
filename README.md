# openclaw-x-video

基于 OpenClaw 多 Agent 架构的自动化视频生产系统。监控 X (Twitter) 爆款内容，自动转化为适合抖音发布的竖屏视频，存储在本地。

---

## 架构概览

```
X 时间线（每小时心跳）
       │
       ▼
┌─────────────┐
│  Scraper    │  Playwright 无头浏览器抓取高互动推文
│  Agent      │  → data/tasks/<ts>_raw.json
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Analyst    │  LLM 分析爆款潜力，判断视频类型
│  Agent      │  → data/tasks/<ts>_task.json
└──────┬──────┘
       │
       ├─── Type A（观点/金句/列表）
       │         │
       │         ▼
       │    Remotion React
       │    文字动画渲染
       │
       └─── Type B（故事/事件）
                 │
                 ▼
            edge-tts + FFmpeg
            配音混剪烧录字幕
                 │
                 ▼
           output/*.mp4
```

三个 Agent 通过 `data/` 目录下的 JSON 文件串行通信，渲染队列 `data/render_queue.json` 保证单任务执行，防止 2C4G 服务器 OOM。

---

## 目录结构

```
openclaw-x-video/
├── config/
│   ├── .env.example        # 所有配置项模板
│   ├── .env                # 实际配置（不提交 git）
│   └── settings.py         # 统一配置加载模块
│
├── agents/
│   ├── scraper/AGENT.md    # Scraper Agent 指令
│   ├── analyst/AGENT.md    # Analyst Agent 指令
│   └── producer/AGENT.md   # Producer Agent 指令
│
├── skills/
│   ├── scraper/
│   │   └── x_scraper.py    # Playwright 抓取脚本
│   ├── analyst/
│   │   └── llm_analyst.py  # LLM 分析脚本
│   ├── queue/
│   │   └── queue_manager.py # 文件锁串行渲染队列
│   ├── remotion/           # Remotion React 项目
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── Root.tsx
│   │   │   └── compositions/TypeA.tsx
│   │   ├── package.json
│   │   ├── remotion.config.ts
│   │   └── render.sh       # 渲染入口脚本
│   └── mixer/
│       └── video_mixer.py  # FFmpeg 混剪脚本
│
├── data/
│   ├── tasks/              # 中转 JSON（raw + task）
│   └── bg_videos/          # 可选：Type B 背景视频素材
│
├── output/                 # 最终 MP4 输出
├── openclaw.json           # OpenClaw Agent 配置
└── setup.sh                # 一键环境安装脚本
```

---

## 视频类型说明

| 类型 | 适用内容 | 渲染方式 | 输出 |
|------|----------|----------|------|
| **Type A** | 观点、金句、列表、数据 | Remotion React 文字动画 | 1080×1920 竖屏 MP4 |
| **Type B** | 故事、事件、有画面感 | edge-tts 配音 + FFmpeg 混剪 | 1080×1920 竖屏 MP4 |

### Type A 任务 JSON 示例

```json
{
  "type": "A",
  "source_tweet_id": "1234567890",
  "title": "硅谷创业者的10条忠告",
  "hook": "99%的人不知道",
  "slides": [
    { "text": "失败是最好的老师", "duration": 2.5 },
    { "text": "专注比努力更重要", "duration": 2.5 }
  ],
  "cta": "关注获取更多",
  "color_scheme": "dark",
  "font_style": "bold"
}
```

### Type B 任务 JSON 示例

```json
{
  "type": "B",
  "source_tweet_id": "9876543210",
  "title": "马斯克凌晨3点的决定",
  "narration_script": "2022年10月，马斯克以440亿美元完成了对推特的收购...",
  "subtitles": [
    { "start": 0.0, "end": 3.5, "text": "2022年10月" },
    { "start": 3.5, "end": 7.0, "text": "马斯克完成推特收购" }
  ],
  "bgm_style": "dramatic",
  "bg_video_keyword": "office night city lights"
}
```

---

## 快速开始

### 1. 环境安装

```bash
# 克隆项目
git clone <repo_url>
cd openclaw-x-video

# 一键安装（Ubuntu/Debian，需 sudo）
bash setup.sh
```

`setup.sh` 会自动完成：
- 安装 FFmpeg、Node.js 20、Python 3
- 创建 Python 虚拟环境并安装依赖
- 安装 Playwright Chromium 浏览器
- 安装 Remotion npm 依赖
- 创建 4G Swap 空间（保障渲染稳定性）
- 生成 `config/.env` 配置文件模板

### 2. 配置 API Key

```bash
vim config/.env
```

必填项：

```dotenv
# LLM API（支持任意 OpenAI-compatible 接口）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-xxxxxxxx
LLM_MODEL=gpt-4o

# X 账号（首次登录后自动保存登录态）
X_USERNAME=your_username
X_PASSWORD=your_password
```

### 3. 激活虚拟环境

```bash
source .venv/bin/activate
```

### 4. 启动 OpenClaw

```bash
openclaw start --config openclaw.json
```

Scraper Agent 每小时自动触发一次完整流程。

---

## 手动运行各阶段

### 单独测试抓取

```bash
source .venv/bin/activate
python skills/scraper/x_scraper.py --limit 10 --min-likes 200
```

### 单独测试 LLM 分析

```bash
python skills/analyst/llm_analyst.py data/tasks/<timestamp>_raw.json
```

### 单独渲染 Type A 视频

```bash
cd skills/remotion
bash render.sh ../../data/tasks/<timestamp>_task.json ../../output/test.mp4
```

### 单独渲染 Type B 视频

```bash
python skills/mixer/video_mixer.py data/tasks/<timestamp>_task.json
```

### 查看渲染队列状态

```bash
python -c "
import sys; sys.path.insert(0, '.')
from skills.queue.queue_manager import status
import json; print(json.dumps(status(), indent=2))
"
```

---

## 背景视频素材（Type B）

将 MP4/MOV 视频放入 `data/bg_videos/` 目录，混剪时会自动循环使用。

若目录为空，系统会用纯黑背景兜底，视频仍可正常生成。

推荐素材来源：[Pexels](https://www.pexels.com/videos/)（免费商用）

---

## 2C4G 服务器优化说明

| 措施 | 配置位置 | 说明 |
|------|----------|------|
| 串行渲染队列 | `skills/queue/queue_manager.py` | 文件锁保证同时只有一个渲染任务 |
| Remotion 单线程 | `remotion.config.ts` + `render.sh` | `--concurrency 1` |
| 4G Swap | `setup.sh` | 渲染峰值内存溢出保障 |
| LLM 上下文修剪 | `openclaw.json` | TTL 5 分钟自动清理旧工具结果 |
| 心跳间隔 1 小时 | `openclaw.json` | 避免频繁调用 API |

---

## 依赖清单

**Python**
- `playwright` — X 内容抓取
- `openai` — LLM API 调用
- `edge-tts` — 免费中文 TTS
- `python-dotenv` — 配置加载

**Node.js**
- `remotion` / `@remotion/cli` — React 视频渲染

**系统**
- `ffmpeg` — 视频合成、字幕烧录
- `chromium` — Playwright 无头浏览器
