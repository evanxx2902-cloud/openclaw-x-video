"""
串行渲染队列管理器（文件锁，防多进程竞争）
render_queue.json 结构:
{
  "current": null | "<task_file_path>",
  "pending": ["path1", "path2"],
  "completed": ["path3"],
  "failed": ["path4"]
}
"""
import fcntl
import json
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import cfg

QUEUE_FILE = cfg.render_queue
LOCK_FILE = cfg.data_dir / ".queue.lock"


def _default_queue() -> dict:
    return {"current": None, "pending": [], "completed": [], "failed": []}


@contextmanager
def _locked():
    lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def read_queue() -> dict:
    if not QUEUE_FILE.exists():
        return _default_queue()
    return json.loads(QUEUE_FILE.read_text())


def _write_queue(q: dict):
    QUEUE_FILE.write_text(json.dumps(q, indent=2))


def enqueue(task_path: str):
    with _locked():
        q = read_queue()
        if task_path not in q["pending"] and task_path != q["current"]:
            q["pending"].append(task_path)
            _write_queue(q)
            print(f"[queue] 入队: {task_path}")


def claim_next() -> str | None:
    """原子性取出下一个任务，有任务正在渲染时返回 None（串行保证）"""
    with _locked():
        q = read_queue()
        if q["current"]:
            return None
        if not q["pending"]:
            return None
        task = q["pending"].pop(0)
        q["current"] = task
        _write_queue(q)
        return task


def mark_done(task_path: str, success: bool):
    with _locked():
        q = read_queue()
        q["current"] = None
        target = q["completed"] if success else q["failed"]
        if task_path not in target:
            target.append(task_path)
        _write_queue(q)
        print(f"[queue] {'完成' if success else '失败'}: {task_path}")


def status() -> dict:
    return read_queue()
