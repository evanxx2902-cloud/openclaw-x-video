#!/bin/bash
# 设置openclaw-x-video定时任务

set -e

cd "$(dirname "$0")"

echo "=== 设置openclaw-x-video定时任务 ===\n"

# 检查当前用户
echo "当前用户: $(whoami)"
echo "项目目录: $(pwd)"

# 创建日志目录
mkdir -p logs
echo "日志目录: $(pwd)/logs"

# 创建虚拟环境激活脚本
cat > .venv_activate.sh << 'EOF'
#!/bin/bash
# 激活虚拟环境
source /root/openclaw-x-video/.venv/bin/activate
cd /root/openclaw-x-video
EOF

chmod +x .venv_activate.sh

# 创建完整流程脚本
cat > run_full_workflow.sh << 'EOF'
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
EOF

chmod +x run_full_workflow.sh

# 创建crontab配置
CRON_JOB="0 * * * * /root/openclaw-x-video/run_full_workflow.sh > /root/openclaw-x-video/logs/cron_$(date +\%Y\%m\%d).log 2>&1"

echo "Cron任务配置:"
echo "$CRON_JOB"
echo ""

# 添加到crontab
if command -v crontab >/dev/null 2>&1; then
    # 备份现有crontab
    crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).bak 2>/dev/null || true
    
    # 添加新任务
    (crontab -l 2>/dev/null | grep -v "run_full_workflow.sh"; echo "$CRON_JOB") | crontab -
    
    echo "✅ Cron任务已添加"
    echo "运行频率: 每小时整点"
    echo "日志文件: logs/cron_YYYYMMDD.log"
else
    echo "⚠️ crontab命令未找到，请手动添加:"
    echo "$CRON_JOB"
fi

# 创建系统状态检查脚本
cat > check_system_status.sh << 'EOF'
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
EOF

chmod +x check_system_status.sh

echo -e "\n✅ 定时任务设置完成！"
echo -e "\n可用命令:"
echo "  ./run_full_workflow.sh    - 运行完整工作流"
echo "  ./check_system_status.sh  - 检查系统状态"
echo "  crontab -l                - 查看定时任务"
echo -e "\n工作流将每小时自动运行一次"
echo "日志文件保存在 logs/ 目录"