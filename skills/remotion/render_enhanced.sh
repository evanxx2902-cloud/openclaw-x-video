#!/bin/bash
# 增强版渲染脚本，支持质量配置
set -e

TASK_JSON="$1"
OUTPUT="$2"
PROFILE="${3:-balanced}"  # 默认使用balanced配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$TASK_JSON" ] || [ -z "$OUTPUT" ]; then
  echo "用法: $0 <task_json> <output_mp4> [profile]"
  echo "可选profile: fast, balanced, high_quality"
  exit 1
fi

# 加载质量配置
if [ -f "render_profiles.json" ]; then
  PROFILE_CONFIG=$(python3 -c "
import json
with open('render_profiles.json') as f:
    config = json.load(f)
profile = config['profiles'].get('$PROFILE', config['profiles'][config['default']])
print(f'--concurrency={profile[\"concurrency\"]}')
print(f'--crf={profile[\"crf\"]}')
  ")
  
  CONCURRENCY=$(echo "$PROFILE_CONFIG" | head -1 | cut -d'=' -f2)
  CRF=$(echo "$PROFILE_CONFIG" | tail -1 | cut -d'=' -f2)
else
  CONCURRENCY=1
  CRF=23
fi

echo "[remotion] 使用配置: $PROFILE (并发: $CONCURRENCY, CRF: $CRF)"

# 计算总帧数
TOTAL_FRAMES=$(python3 -c "
import json
t = json.load(open('$TASK_JSON'))
fps = 30
frames = int(1.5 * fps)  # 开场
for s in t.get('slides', []):
    frames += int(s['duration'] * fps)
frames += int(2.0 * fps)  # 结尾
print(frames)
")

# 构建props JSON
PROPS=$(python3 -c "
import json
t = json.load(open('$TASK_JSON'))
props = {
    'hook': t.get('hook', ''),
    'slides': t.get('slides', []),
    'cta': t.get('cta', ''),
    'colorScheme': t.get('color_scheme', 'dark'),
    'fontStyle': t.get('font_style', 'bold'),
}
print(json.dumps(props))
")

cd "$SCRIPT_DIR"

# 确保依赖已安装
if [ ! -d "node_modules" ]; then
  echo "[remotion] 安装依赖..."
  npm install --silent
fi

# 渲染视频
echo "[remotion] 开始渲染..."
npx remotion render \
  src/index.ts \
  TypeA \
  --props="$PROPS" \
  --duration-in-frames="$TOTAL_FRAMES" \
  --concurrency="$CONCURRENCY" \
  --crf="$CRF" \
  --codec="h264" \
  --muted \
  --overwrite \
  --output="$OUTPUT"

# 检查输出文件
if [ -f "$OUTPUT" ]; then
  FILESIZE=$(stat -c%s "$OUTPUT")
  FILESIZE_MB=$(echo "scale=2; $FILESIZE / 1048576" | bc)
  echo "[remotion] 渲染完成: $OUTPUT (${FILESIZE_MB} MB)"
else
  echo "[remotion] 错误: 输出文件未生成"
  exit 1
fi
