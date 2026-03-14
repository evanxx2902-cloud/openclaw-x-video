"""
监控和日志配置
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logging(name="openclaw-x-video", level=logging.INFO):
    """设置日志配置"""
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建文件处理器
    log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # 配置根日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 移除现有处理器
    logger.handlers.clear()
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_system_stats():
    """获取系统统计信息"""
    import psutil
    from pathlib import Path
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "system": {}
    }
    
    try:
        # CPU使用率
        stats["system"]["cpu_percent"] = psutil.cpu_percent(interval=1)
        stats["system"]["cpu_count"] = psutil.cpu_count()
        
        # 内存使用
        memory = psutil.virtual_memory()
        stats["system"]["memory_total_gb"] = round(memory.total / (1024**3), 2)
        stats["system"]["memory_used_gb"] = round(memory.used / (1024**3), 2)
        stats["system"]["memory_percent"] = memory.percent
        
        # 磁盘使用
        disk = psutil.disk_usage(PROJECT_ROOT)
        stats["system"]["disk_total_gb"] = round(disk.total / (1024**3), 2)
        stats["system"]["disk_used_gb"] = round(disk.used / (1024**3), 2)
        stats["system"]["disk_percent"] = disk.percent
        
    except ImportError:
        stats["system"]["error"] = "psutil not installed"
    
    return stats

def get_project_stats():
    """获取项目统计信息"""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "project": {}
    }
    
    # 任务文件统计
    tasks_dir = PROJECT_ROOT / "data" / "tasks"
    if tasks_dir.exists():
        task_files = list(tasks_dir.glob("*.json"))
        stats["project"]["total_tasks"] = len(task_files)
        
        raw_files = [f for f in task_files if "_raw.json" in f.name]
        task_files = [f for f in task_files if "_task.json" in f.name]
        
        stats["project"]["raw_files"] = len(raw_files)
        stats["project"]["task_files"] = len(task_files)
    
    # 输出文件统计
    output_dir = PROJECT_ROOT / "output"
    if output_dir.exists():
        video_files = list(output_dir.glob("*.mp4"))
        stats["project"]["videos_generated"] = len(video_files)
        
        if video_files:
            total_size = sum(f.stat().st_size for f in video_files)
            stats["project"]["total_video_size_mb"] = round(total_size / (1024**2), 2)
    
    # 日志文件统计
    if LOG_DIR.exists():
        log_files = list(LOG_DIR.glob("*.log"))
        stats["project"]["log_files"] = len(log_files)
    
    return stats

def check_queue_status():
    """检查队列状态"""
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from skills.queue.queue_manager import status
        
        queue_stats = status()
        return {
            "timestamp": datetime.now().isoformat(),
            "queue": queue_stats
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "queue": {"error": str(e)}
        }

def generate_monitoring_report():
    """生成监控报告"""
    report = {
        "system": get_system_stats(),
        "project": get_project_stats(),
        "queue": check_queue_status()
    }
    
    # 保存报告
    report_file = LOG_DIR / f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    
    return report

if __name__ == "__main__":
    # 测试监控功能
    logger = setup_logging()
    logger.info("启动监控系统")
    
    report = generate_monitoring_report()
    logger.info(f"监控报告已生成: {len(str(report))} 字节")
    
    print("监控系统测试完成")
    print(f"日志目录: {LOG_DIR}")
    print(f"系统状态: CPU {report['system']['system'].get('cpu_percent', 'N/A')}%")
    print(f"项目状态: {report['project']['project'].get('videos_generated', 0)} 个视频")