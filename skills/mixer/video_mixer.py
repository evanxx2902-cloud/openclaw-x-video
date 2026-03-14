"""
Type B 视频混剪器
流程: TTS 生成音频 → 选取/生成背景视频 → FFmpeg 合成 → 烧录字幕
用法: python video_mixer.py <task_json_path>
"""
import asyncio
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import cfg

try:
    import edge_tts
except ImportError:
    print("[mixer] 请安装 edge-tts: pip install edge-tts")
    sys.exit(1)


async def tts_generate(text: str, output_path: Path):
    communicate = edge_tts.Communicate(
        text=text,
        voice=cfg.tts_voice,
        rate=cfg.tts_rate,
    )
    await communicate.save(str(output_path))
    print(f"[mixer] TTS 生成: {output_path}")


def get_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(audio_path)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(result.stdout)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio":
            return float(stream.get("duration", 0))
    return 0.0


def build_srt(subtitles: list[dict], srt_path: Path):
    lines = []
    for i, sub in enumerate(subtitles, 1):
        start = _sec_to_srt(sub["start"])
        end = _sec_to_srt(sub["end"])
        lines.append(f"{i}\n{start} --> {end}\n{sub['text']}\n")
    srt_path.write_text("\n".join(lines), encoding="utf-8")


def _sec_to_srt(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def get_or_create_bg_video(keyword: str, duration: float, output_path: Path) -> Path:
    """
    优先使用 data/bg_videos/ 中的本地视频，否则生成纯色背景兜底。
    生产环境可接入 Pexels API 替换此函数。
    """
    bg_dir = cfg.data_dir / "bg_videos"
    bg_dir.mkdir(exist_ok=True)

    candidates = list(bg_dir.glob("*.mp4")) + list(bg_dir.glob("*.mov"))
    if candidates:
        src = candidates[0]
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(src),
            "-t", str(duration),
            "-c", "copy",
            str(output_path),
        ], check=True, capture_output=True)
        return output_path

    # 兜底：生成纯黑背景视频
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s=1080x1920:r=30:d={duration}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ], check=True, capture_output=True)
    print(f"[mixer] 使用纯黑背景（可将视频放入 data/bg_videos/ 替换）")
    return output_path


def mix(task: dict, output_path: Path):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        audio_path = tmp / "narration.mp3"
        bg_path = tmp / "bg.mp4"
        srt_path = tmp / "subs.srt"

        # 1. TTS
        asyncio.run(tts_generate(task["narration_script"], audio_path))
        duration = get_audio_duration(audio_path)
        if duration <= 0:
            raise RuntimeError("TTS 音频时长为 0，请检查 edge-tts 配置")

        # 2. 背景视频
        get_or_create_bg_video(task.get("bg_video_keyword", ""), duration, bg_path)

        # 3. 字幕文件
        build_srt(task.get("subtitles", []), srt_path)

        # 4. FFmpeg 合成：视频 + 音频 + 字幕
        subtitle_filter = f"subtitles={srt_path}:force_style='FontName=Noto Sans SC,FontSize=18,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Alignment=2'"
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(bg_path),
            "-i", str(audio_path),
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_path),
        ], check=True)

    print(f"[mixer] 混剪完成: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python video_mixer.py <task_json_path>")
        sys.exit(1)

    task_path = Path(sys.argv[1])
    task = json.loads(task_path.read_text())

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = task.get("title", "video").replace(" ", "_")[:20]
    out = cfg.output_dir / f"{ts}_{title}.mp4"

    mix(task, out)
