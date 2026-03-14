#!/bin/bash
# 完整工作流脚本
set -e

cd /root/openclaw-x-video
source .venv/bin/activate

TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="logs/workflow_${TIMESTAMP}.log"

echo "=== 开始完整工作流 $(date) ===" | tee -a "$LOG_FILE"

# 1. 抓取数据
echo "[1/4] 抓取数据..." | tee -a "$LOG_FILE"
python skills/scraper/x_scraper_smart.py --limit 20 --min-likes 500 2>&1 | tee -a "$LOG_FILE"

# 查找最新的raw文件
LATEST_RAW=$(ls -t data/tasks/*_raw.json 2>/dev/null | head -1)

if [ -z "$LATEST_RAW" ]; then
    echo "错误: 未找到raw文件" | tee -a "$LOG_FILE"
    exit 1
fi

echo "使用raw文件: $LATEST_RAW" | tee -a "$LOG_FILE"

# 2. LLM分析
echo "[2/4] LLM分析..." | tee -a "$LOG_FILE"
python skills/analyst/llm_analyst.py "$LATEST_RAW" 2>&1 | tee -a "$LOG_FILE"

# 生成的任务文件
TASK_FILE="${LATEST_RAW/_raw.json/_task.json}"

if [ ! -f "$TASK_FILE" ]; then
    echo "错误: 未生成task文件" | tee -a "$LOG_FILE"
    exit 1
fi

echo "生成任务文件: $TASK_FILE" | tee -a "$LOG_FILE"

# 3. 加入队列
echo "[3/4] 加入渲染队列..." | tee -a "$LOG_FILE"
python -c "
import sys
sys.path.insert(0, '.')
from skills.queue.queue_manager import enqueue
enqueue('$TASK_FILE')
print('任务已加入队列: $TASK_FILE')
" 2>&1 | tee -a "$LOG_FILE"

# 4. 处理队列（如果有任务）
echo "[4/4] 检查渲染队列..." | tee -a "$LOG_FILE"
python -c "
import sys
sys.path.insert(0, '.')
from skills.queue.queue_manager import claim_next, mark_done, status
import json

# 检查队列状态
queue_status = status()
print('当前队列状态:')
print(json.dumps(queue_status, indent=2))

# 如果有pending任务，处理第一个
if queue_status['pending']:
    next_task = claim_next()
    if next_task:
        print(f'开始渲染任务: {next_task}')
        # 这里可以调用渲染脚本
        # 暂时标记为完成（模拟）
        mark_done(next_task, True)
        print('任务渲染完成（模拟）')
else:
    print('没有待处理任务')
" 2>&1 | tee -a "$LOG_FILE"

echo "=== 工作流完成 $(date) ===" | tee -a "$LOG_FILE"
echo "日志文件: $LOG_FILE"
