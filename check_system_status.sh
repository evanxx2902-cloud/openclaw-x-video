#!/bin/bash
# 检查系统状态
cd /root/openclaw-x-video

echo "=== 系统状态检查 $(date) ==="
echo ""

# 1. 检查Python环境
echo "1. Python环境:"
source .venv/bin/activate
python --version
python -c "import playwright, openai, edge_tts; print('✓ 核心依赖正常')"

# 2. 检查Node.js环境
echo -e "\n2. Node.js环境:"
node --version
cd skills/remotion && npm list --depth=0 | grep -E "(remotion|@remotion)" && cd ../..

# 3. 检查目录结构
echo -e "\n3. 目录结构:"
ls -la data/tasks/ | head -5
echo "任务文件数量: $(ls data/tasks/*.json 2>/dev/null | wc -l)"
ls -la output/ | head -5
echo "输出视频数量: $(ls output/*.mp4 2>/dev/null | wc -l)"

# 4. 检查队列状态
echo -e "\n4. 队列状态:"
python -c "
import sys
sys.path.insert(0, '.')
from skills.queue.queue_manager import status
import json
print(json.dumps(status(), indent=2))
"

# 5. 检查日志文件
echo -e "\n5. 日志文件:"
ls -la logs/ | head -5
echo "最新日志:"
tail -5 logs/*.log 2>/dev/null | tail -5 || echo "暂无日志"

# 6. 检查cron任务
echo -e "\n6. Cron任务:"
crontab -l | grep -A2 -B2 "openclaw-x-video" || echo "未找到相关cron任务"

echo -e "\n=== 检查完成 ==="
