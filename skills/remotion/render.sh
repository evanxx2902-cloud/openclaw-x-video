#!/bin/bash
# 用法: bash render.sh <task_json_path> <output_mp4_path>
# 从 task JSON 提取参数，调用 remotion render
set -e

TASK_JSON="$1"
OUTPUT="$2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$TASK_JSON" ] || [ -z "$OUTPUT" ]; then
  echo "用法: $0 <task_json> <output_mp4>"
  exit 1
fi

# 计算总帧数
TOTAL_FRAMES=$(python3 -c "
import json
t = json.load(open('$TASK_JSON'))
fps = 30
frames = int(1.5 * fps)
for s in t.get('slides', []):
    frames += int(s['duration'] * fps)
frames += int(2.0 * fps)
print(frames)
")

# 构建 props JSON
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

npx remotion render \
  --composition TypeA \
  --props "$PROPS" \
  --frames "0-$((TOTAL_FRAMES - 1))" \
  --concurrency "${REMOTION_CONCURRENCY:-1}" \
  --output "$OUTPUT"

echo "[remotion] 渲染完成: $OUTPUT"
