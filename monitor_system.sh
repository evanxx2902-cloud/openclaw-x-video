#!/bin/bash
# 系统监控脚本

set -e

cd "$(dirname "$0")"

echo "=== openclaw-x-video 系统监控 ===\n"

# 激活虚拟环境
source .venv/bin/activate

# 运行监控
python -c "
import sys
sys.path.insert(0, '.')
from config.monitoring_config import generate_monitoring_report, setup_logging
import json

logger = setup_logging()
report = generate_monitoring_report()

print('📊 系统监控报告')
print('=' * 50)

# 系统信息
sys_info = report['system']['system']
print(f'系统资源:')
print(f'  CPU使用率: {sys_info.get(\"cpu_percent\", \"N/A\")}% ({sys_info.get(\"cpu_count\", \"N/A\")}核心)')
print(f'  内存使用: {sys_info.get(\"memory_used_gb\", \"N/A\")}/{sys_info.get(\"memory_total_gb\", \"N/A\")} GB ({sys_info.get(\"memory_percent\", \"N/A\")}%)')
print(f'  磁盘使用: {sys_info.get(\"disk_used_gb\", \"N/A\")}/{sys_info.get(\"disk_total_gb\", \"N/A\")} GB ({sys_info.get(\"disk_percent\", \"N/A\")}%)')

# 项目信息
proj_info = report['project']['project']
print(f'\n📁 项目状态:')
print(f'  任务文件: {proj_info.get(\"raw_files\", 0)} raw, {proj_info.get(\"task_files\", 0)} task')
print(f'  生成视频: {proj_info.get(\"videos_generated\", 0)} 个')
if 'total_video_size_mb' in proj_info:
    print(f'  视频总大小: {proj_info[\"total_video_size_mb\"]} MB')
print(f'  日志文件: {proj_info.get(\"log_files\", 0)} 个')

# 队列信息
queue_info = report['queue']['queue']
print(f'\n🔄 队列状态:')
print(f'  当前任务: {queue_info.get(\"current\", \"无\")}')
print(f'  等待中: {len(queue_info.get(\"pending\", []))} 个')
print(f'  已完成: {len(queue_info.get(\"completed\", []))} 个')
print(f'  已失败: {len(queue_info.get(\"failed\", []))} 个')

print(f'\n⏰ 检查时间: {report[\"system\"][\"timestamp\"]}')
print('=' * 50)

logger.info('系统监控检查完成')
"

echo -e "\n📈 监控命令:"
echo "  ./monitor_system.sh          # 查看系统状态"
echo "  tail -f logs/*.log           # 查看实时日志"
echo "  ls -la logs/monitoring_*.json # 查看历史监控报告"

echo -e "\n🔄 自动监控:"
echo "  每小时自动运行完整工作流"
echo "  监控报告保存在 logs/ 目录"