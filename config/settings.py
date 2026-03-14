"""统一配置加载，所有脚本通过 from config.settings import cfg 使用"""
import os
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).parent.parent
load_dotenv(_root / "config" / ".env", override=False)
load_dotenv(_root / ".env", override=False)


class _Cfg:
    # 路径
    project_root: Path = _root
    data_dir: Path = Path(os.getenv("DATA_DIR") or str(_root / "data"))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR") or str(_root / "output"))

    @property
    def tasks_dir(self) -> Path:
        return self.data_dir / "tasks"

    @property
    def render_queue(self) -> Path:
        return self.data_dir / "render_queue.json"

    # LLM
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")

    # X 账号
    x_username: str = os.getenv("X_USERNAME", "")
    x_password: str = os.getenv("X_PASSWORD", "")

    # TTS
    tts_voice: str = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
    tts_rate: str = os.getenv("TTS_RATE", "+10%")

    # Remotion
    remotion_concurrency: int = int(os.getenv("REMOTION_CONCURRENCY", "1"))


cfg = _Cfg()

# 确保运行时目录存在
for _d in [cfg.data_dir, cfg.tasks_dir, cfg.output_dir]:
    _d.mkdir(parents=True, exist_ok=True)
